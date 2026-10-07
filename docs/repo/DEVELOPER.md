# Developer Setup

For `TypeScript`, frontend apps, and `Prisma`:

```sh
pnpm install
```

For `Python` and backend apps:

```sh
python3 -m venv .venv
source .venv/bin/activate
pip install -e "packages/python[dev]"
```

At root create:

- `.env.prod`
- `.env.local`

Switch between which `.env` is used with:

```sh
pnpm use:[prod|local]
```

Create symbolic links to each app and Prisma:

```sh
./scripts/load-symbolic-links.sh
```
