import io
import json
import os
import sys
import traceback
import base64

stdout_buf = io.StringIO()
stderr_buf = io.StringIO()

orig_stdout = sys.stdout
orig_stderr = sys.stderr
sys.stdout = stdout_buf
sys.stderr = stderr_buf

exit_code = 0
artifacts = []

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
            for i, fig in enumerate(figs):
                buf = io.BytesIO()
                fig.savefig(buf, format="png", bbox_inches="tight")
                buf.seek(0)
                artifact = {
                    "type": "image",
                    "data": base64.b64encode(buf.read()).decode("ascii"),
                    "metadata": {
                        "format": "png",
                        "index": str(i)
                    }
                }
                artifacts.append(artifact)
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
    "artifacts": artifacts,
    "exit_code": exit_code,
}

print(json.dumps(result))