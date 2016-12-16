from tools_lib.host_info import DEBUG

# ============================================
# mongoengine
# ============================================
MONGODB_NAME = 'app_center'

# ==================
if DEBUG:
    settings = {
        "debug": True,
        "autoreload": True
    }
else:
    settings = {
        "autoreload": False
    }
