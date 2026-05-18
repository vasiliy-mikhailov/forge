# reward-bench — rebar3 via dockerised dev image.
# Everything runs inside reward-bench-dev:0.1 so the host doesn't
# need Erlang/OTP installed. A named docker volume caches rebar3
# fetched deps across invocations.

LAB_DIR      := $(shell pwd)
DEV_IMAGE    := reward-bench-dev:0.1
CACHE_VOLUME := reward-bench-rebar3-cache

REBAR3 := docker run --rm \
    -v $(LAB_DIR):/work \
    -v $(CACHE_VOLUME):/root/.cache/rebar3 \
    -w /work \
    $(DEV_IMAGE) rebar3

REBAR3_TTY := docker run --rm -it \
    -v $(LAB_DIR):/work \
    -v $(CACHE_VOLUME):/root/.cache/rebar3 \
    -w /work \
    $(DEV_IMAGE) rebar3

.PHONY: dev-image compile eunit ct shell dialyzer release clean

dev-image: Dockerfile.dev
	docker build -t $(DEV_IMAGE) -f Dockerfile.dev .

compile: dev-image
	$(REBAR3) compile

eunit: dev-image
	$(REBAR3) eunit

ct: dev-image
	$(REBAR3) ct --readable=true

shell: dev-image
	$(REBAR3_TTY) shell

dialyzer: dev-image
	$(REBAR3) dialyzer

release: dev-image
	$(REBAR3) as prod release

clean:
	rm -rf _build rebar.lock
