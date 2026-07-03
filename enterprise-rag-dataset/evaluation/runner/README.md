# Automated Onyx Evaluation Runner

## Security

The runner talks to `http://127.0.0.1:8088` through an SSH tunnel. Do not point it at the public HTTP address because a PAT is a bearer credential.

Place the full token on one line in `D:\企业级项目搭建\.secrets\onyx_pat.txt`. The `.secrets` directory is excluded from Git.

## Run

Start the encrypted tunnel:

```powershell
ssh -N -L 8088:127.0.0.1:80 -i "D:\企业级项目搭建\onyx_key.pem" ubuntu@146.56.217.22
```

Run a three-question smoke test in another PowerShell window:

```powershell
python D:\企业级项目搭建\enterprise-rag-dataset\evaluation\runner\run_eval.py --limit 3
```

Run all 50 questions with four concurrent workers by removing `--limit 3`.
Use `--workers 1` for a sequential diagnostic run.
