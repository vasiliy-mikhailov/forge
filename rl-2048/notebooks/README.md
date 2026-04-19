The notebooks folder is bind-mounted into the container as
`/workspace/notebooks`.

I don't commit `.ipynb` files — they accumulate secrets, large outputs,
and random absolute paths quickly. Once a pipeline stabilizes, I extract
it into a `.py` module and commit that.
