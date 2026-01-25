from q_engine import hot_reload, bootstrap

def fallback_tick(*args, **kwargs):
    pass
def tick_fc():
    from q_engine.bootstrap import get_tick
    return get_tick()
tick = tick_fc()

def reload(event):
    if not event.src_path.endswith('.py'):
        return
    global tick
    hot_reload.reload(__file__)
    tick = tick_fc()
hot_reload.watch(reload)

def dispatch(*args, **kwargs):
    global tick
    try:
        tick(*args, **kwargs)
    except Exception as e:
        tick = fallback_tick
        import traceback
        traceback.print_exception(e)

run = bootstrap.get_run()
run(dispatch)
