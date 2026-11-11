#!/usr/bin/env python3
"""Synthetic, read-only contract checks against the organizer's actual train SDK.

Does not inspect any sample state or scenario JSONL and does not modify the SDK.
Run from authorized workspace:
    python tools/verify_sdk_contract.py --data-root path/to/train+public_test
"""
from __future__ import annotations
import argparse
import json
import sys
from pathlib import Path


def main():
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--data-root',type=Path,required=True)
    opts=parser.parse_args()
    sdk_parent=opts.data_root/'train'
    catalog_path=sdk_parent/'train_tools_catalog.json'
    if not catalog_path.is_file() or not (sdk_parent/'zaic_tools'/'executor.py').is_file():
        parser.error('Missing train catalog or zaic_tools under --data-root/train')
    sys.path.insert(0,str(sdk_parent.resolve()))
    from zaic_tools.executor import Session
    from zaic_tools.apps import TOOLS
    from zaic_tools.utils import state_hash
    catalog=json.loads(catalog_path.read_text(encoding='utf-8'))
    catalog_names={t['name'] for a in catalog['apps'] for t in a['tools']}
    missing=catalog_names-set(TOOLS)
    assert not missing, f'Catalog tool(s) missing from SDK: {sorted(missing)}'
    entry={
      '_meta': {'question_id':'synthetic_001','current_time':'2026-11-09T16:00:00+07:00',
                'tools':['smart_home.light_set','smart_home.get_status','food_delivery.place_order',
                         'ride_hailing.book','sys.ask_missing_info','sms.send']},
      'smart_home':{'devices':[{'id':'light_01','type':'light','room':'phòng khách','state':{'power':'off'}}]},
      'food_delivery':{'restaurants':[{'id':'rest_01','menu':[{'id':'food_01','name':'cơm','price':35000}]}],'orders':[]},
      'ride_hailing':{'rides':[]},
      'sms':{'messages':[]},
    }
    env=Session('synthetic_001',entry,catalog)
    assert env.validate('smart_home.light_set',{'device_id':'not-real','power':'on'})['ok']
    assert env.get_tool_calls()==[], 'validate() should not log'
    r=env.call('smart_home.light_set',{'device_id':'not-real','power':'on'})
    assert r.get('ok') is True and r.get('done') is False, f'x-ref no-op changed: {r}'
    assert env.validate('food_delivery.place_order',{'restaurant_id':'rest_01','items':[{}]})['ok']
    r=env.call('food_delivery.place_order',{'restaurant_id':'rest_01','items':[{}]})
    assert r.get('ok') is True and r.get('done') is False, f'nested no-op changed: {r}'
    assert env.validate('sys.ask_missing_info',{'tool_name':'sms.send'})['ok'] is False
    before=env.get_state_hash()
    r=env.call('sys.ask_missing_info',{'tool_name':'sms.send','params':['phone_number']})
    assert r.get('waiting_for_user') is True and env.get_state_hash()==before
    r=env.call('ride_hailing.book',{'pickup':'home','dropoff':'work','vehicle':'bike','schedule_time':'2026-11-09T15:00:00+07:00'})
    assert r.get('ok') is True and 'schedule_time' not in r['item'], 'past ride must be immediate'
    n=len(env.get_tool_calls())
    r=env.call('smart_home.light_set',{'power':'on'})
    assert r.get('ok') is False and len(env.get_tool_calls())==n+1, 'invalid call must be logged'
    a={'sms':{'messages':[{'id':'msg_1','content':'Alpha'}]}}
    b={'sms':{'messages':[{'id':'msg_1','content':'Beta'}]}}
    assert state_hash(a)==state_hash(b), 'text fields should be ignored by hash'
    print(json.dumps({'status':'PASS','sdk':'train','catalog_tools':len(catalog_names),
        'checks':['coverage','validate-no-log','xref-business-noop','nested-validation-gap',
                  'ask-no-state-change','past-ride-immediate','invalid-call-logged','hash-ignores-freetext']},
        ensure_ascii=False,indent=2))

if __name__=='__main__':
    main()
