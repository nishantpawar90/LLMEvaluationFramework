from deepeval.tracing import observe, update_current_trace, trace_manager
import json

trace_manager.clear_traces()

def f():
    update_current_trace(output='ANS')
    return 'ok'

f = observe(name='test-fn')(f)
res = f()
print('res=', res)
print(json.dumps(trace_manager.get_all_traces_dict(), default=str))
