import os

os.environ.setdefault("DATABASE_URL", "postgresql://ci:ci@localhost:5432/life")
os.environ.setdefault("TOKEN_ENCRYPTION_KEY", "Cf_EfMeK40J6EokzO2GMyNUllKWcBGMqqoxzKYFJRM8=")
os.environ.setdefault("SESSION_SECRET", "ci-placeholder")
