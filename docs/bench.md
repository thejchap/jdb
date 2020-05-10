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

### 2020-05-09
added lmdb
```bash
key_size=24 set_size=1000000 store=jdb thread_count=32 val_size=8
elapsed=51.27223068

key_size=24 set_size=1000000 store=redis thread_count=32 val_size=8
elapsed=11.052644085999999

key_size=24 set_size=1000000 store=lmdb thread_count=32 val_size=8
elapsed=53.547044742
```