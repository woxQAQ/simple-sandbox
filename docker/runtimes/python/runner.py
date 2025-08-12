import io
import json
import os
import sys
import traceback
import base64

# Ensure headless backend
os.environ["MPLBACKEND"] = "Agg"

stdout_buf = io.StringIO()
stderr_buf = io.StringIO()

orig_stdout = sys.stdout
orig_stderr = sys.stderr
sys.stdout = stdout_buf
sys.stderr = stderr_buf

exit_code = 0
images = []

try:
    code_path = os.path.join("/workspace", "main.py")
    g = {"__name__": "__main__"}
    with open(code_path, "r", encoding="utf-8") as f:
        code = f.read()
    try:
        import matplotlib
        import matplotlib.pyplot as plt
    except Exception:
        matplotlib = None
        plt = None

    exec(compile(code, code_path, "exec"), g)

    if plt is not None:
        try:
            from matplotlib._pylab_helpers import Gcf
            figs = [fm.canvas.figure for fm in Gcf.get_all_fig_managers()]
            for fig in figs:
                buf = io.BytesIO()
                fig.savefig(buf, format="png", bbox_inches="tight")
                buf.seek(0)
                images.append(base64.b64encode(buf.read()).decode("ascii"))
                plt.close(fig)
        except Exception:
            # do not crash if capture fails
            pass
except SystemExit as e:
    try:
        exit_code = int(e.code) if isinstance(e.code, int) else 1
    except Exception:
        exit_code = 1
except Exception:
    exit_code = 1
    traceback.print_exc()
finally:
    sys.stdout = orig_stdout
    sys.stderr = orig_stderr

result = {
    "stdout": stdout_buf.getvalue(),
    "stderr": stderr_buf.getvalue(),
    "images_b64": images,
    "exit_code": exit_code,
}

print(json.dumps(result)) 