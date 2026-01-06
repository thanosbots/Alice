import time

_st = time.time()

def _gu():
    _s = int(time.time() - _st)
    _m, _s = divmod(_s, 60)
    _h, _m = divmod(_m, 60)
    _d, _h = divmod(_h, 24)

    if _d > 0:
        return f"{_d}d {_h}h {_m}m {_s}s"
    elif _h > 0:
        return f"{_h}h {_m}m {_s}s"
    elif _m > 0:
        return f"{_m}m {_s}s"
    else:
        return f"{_s}s"

def _sd(_t: str) -> str:
    _mp = str.maketrans("0123456789", "𝟢𝟣𝟤𝟥𝟦𝟧𝟨𝟩𝟪𝟫")
    return str(_t).translate(_mp)
