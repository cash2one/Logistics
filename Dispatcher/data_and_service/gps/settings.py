from tools_lib.host_info import DEBUG

if DEBUG:
    settings = {
        "debug": True,
        "autoreload": True
    }
else:
    settings = {
        "autoreload": False
    }
