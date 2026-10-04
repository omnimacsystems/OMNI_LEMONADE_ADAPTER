import copy
import json
import pathlib
import tempfile
import unittest
from adapter.core import Documents, Hold, prefill_budget, loop_signature, strict_json, run
from adapter.runtime import Client
from adapter.verifier import verify_candidate, finish_gate

ROOT=pathlib.Path(__file__).resolve().parent.parent
CONFIG=json.loads((ROOT/'config/agent.json').read_text())
DOCS=json.loads((ROOT/'corpus/documents.json').read_text())
KEY=json.loads((ROOT/'corpus/answer_key.json').read_text())
ACTION={"type":"action","name":"read_document","arguments":{"document_id":"DOC_A"}}
FINAL={"type":"final",**KEY}


class Fake:
    model='synthetic';fingerprint='synthetic';mode='normal'
    def __init__(self, mode):self.mode=mode;self.calls=0;self.prompts=[]
    def request(self,route,data,timeout):
        if route=='tokenize':
            self.prompts.append(data['content'])
            return {'tokens':[1]*(4000 if self.mode=='budget' else 10)}
        assert data['prompt']==self.prompts[-1]
        self.calls+=1
        text=json.dumps(ACTION if self.calls==1 or self.mode=='loop' else FINAL)
        if self.mode=='unknown':text='{"type":"action","name":"shell","arguments":{}}'
        return {'model':self.model,'system_fingerprint':'foreign' if self.mode=='identity' else self.fingerprint,'choices':[{'text':text,'finish_reason':'length' if self.mode=='length' else 'stop'}],
                'usage':{'prompt_tokens':11 if self.mode=='mismatch' else 10,'completion_tokens':512 if self.mode=='length' else 20}}


class Contracts(unittest.TestCase):
    def test_budget_boundary(self):
        prefill_budget(3328,CONFIG['execution_budget'])
        with self.assertRaises(Hold):prefill_budget(3329,CONFIG['execution_budget'])

    def test_tools_and_path_denial(self):
        d=Documents(DOCS)
        self.assertEqual(len(d.call({'type':'action','name':'list_documents','arguments':{}})),2)
        for path in ['../secret','C:/secret','https://example.com','DOC_A/../DOC_B']:
            with self.assertRaises(Hold):d.call({**ACTION,'arguments':{'document_id':path}})
        for name in ['shell','write','browser','execute']:
            with self.assertRaises(Hold):d.call({**ACTION,'name':name})

    def test_signature_and_strict_json(self):
        self.assertEqual(loop_signature(ACTION),loop_signature(dict(reversed(list(ACTION.items())))))
        with self.assertRaises(Hold):strict_json('{"type":"final","type":"action"}')

    def test_verifier_requires_read_and_exact_evidence(self):
        self.assertEqual(verify_candidate(FINAL,KEY,{})['verdict'],'FAIL')
        self.assertEqual(verify_candidate(FINAL,KEY,{'DOC_A':DOCS['DOC_A']})['verdict'],'PASS')
        self.assertEqual(verify_candidate({**FINAL,'answer':'red'},KEY,{'DOC_A':DOCS['DOC_A']})['verdict'],'FAIL')
        for args in [({'verdict':'FAIL'},True,True,True),({'verdict':'PASS'},False,True,True),({'verdict':'PASS'},True,False,True),({'verdict':'PASS'},True,True,False)]:
            self.assertFalse(finish_gate(*args))

    def test_network_boundary(self):
        for ep in ['http://example.com/v1','http://localhost:13315/v1','http://127.0.0.1:13315/v1?x=1','http://u:p@127.0.0.1:13315/v1']:
            with self.assertRaises(Hold):Client(ep,'x','x')
        with self.assertRaises(Hold):Client('http://127.0.0.1:13315/v1','x','x').request('shell')

    def test_trajectories(self):
        for mode,reason in [('normal',None),('loop','LOOP_SIGNATURE'),('budget','PREFILL_BUDGET'),('length','TRUNCATED'),('mismatch','TOKEN_COUNT_DIVERGENCE'),('unknown','UNKNOWN_ACTION_OR_DOCUMENT'),('identity','RUNTIME_IDENTITY')]:
            with self.subTest(mode=mode),tempfile.TemporaryDirectory() as out:
                c=Fake(mode);report,folder=run('NORMAL_SUCCESS',c,'{{messages}}',copy.deepcopy(CONFIG),DOCS,KEY,out,{})
                self.assertEqual(report['hold_reason'],reason)
                self.assertLessEqual(c.calls,3)
                self.assertEqual(report['final_verdict'],'PASS' if mode=='normal' else 'HOLD')
                self.assertTrue((folder/'SEAL.json').exists())
                if mode=='budget':self.assertEqual(c.calls,0)
                if mode=='loop':self.assertEqual(report['tool_calls'],1)
                if mode in ['length','mismatch']:self.assertTrue((folder/'raw-output-1.txt').exists())

    def test_call_limits_and_timeout(self):
        for field,value,reason in [('max_model_calls',1,'MODEL_CALL_BUDGET'),('max_tool_calls',0,'TOOL_CALL_BUDGET'),('total_timeout',0,'TIMEOUT')]:
            with self.subTest(field=field),tempfile.TemporaryDirectory() as out:
                cfg=copy.deepcopy(CONFIG);cfg['execution_budget'][field]=value
                c=Fake('normal');report,_=run('NORMAL_SUCCESS',c,'{{messages}}',cfg,DOCS,KEY,out,{})
                self.assertEqual(report['hold_reason'],reason)
                if field=='total_timeout':self.assertEqual(c.calls,0)

    def test_runtime_hash_rejects_before_network(self):
        from adapter.runtime import preflight
        with tempfile.TemporaryDirectory() as root:
            pathlib.Path(root,'bad.exe').write_bytes(b'not the expected binary')
            with self.assertRaisesRegex(Hold,'RUNTIME_FILE_HASH'):
                preflight(None,{'files':[{'root':'backend','path':'bad.exe','sha256':'0'*64}]},root,root,'unused')

    def test_seal_tamper_detection(self):
        from adapter.core import digest
        with tempfile.TemporaryDirectory() as out:
            _,folder=run('NORMAL_SUCCESS',Fake('normal'),'{{messages}}',copy.deepcopy(CONFIG),DOCS,KEY,out,{})
            seal=json.loads((folder/'SEAL.json').read_text())
            self.assertTrue(all(digest((folder/k).read_bytes())==v for k,v in seal.items()))
            (folder/'raw-output-1.txt').write_text('tampered')
            self.assertNotEqual(digest((folder/'raw-output-1.txt').read_bytes()),seal['raw-output-1.txt'])


if __name__=='__main__':unittest.main()
