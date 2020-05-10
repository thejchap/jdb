# bench
## overview
just keeping track of results/evolution

### setup
```bash
redis-server --save "" --appendonly no
```

## results
### 2020-05-07
```bash
key_size=24 set_size=1000000 store=jdb thread_count=32 val_size=8
elapsed=56.308610462000004
key_size=24 set_size=1000000 store=redis thread_count=32 val_size=8
elapsed=10.670338552
```