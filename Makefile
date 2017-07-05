SOURCES := $(shell echo src/*.py src/*/__main__.py)
TARGETS := $(patsubst src/%.py,templates/%.json,$(patsubst src/%/__main__.py,templates/%.json,$(SOURCES)))

all: $(TARGETS)

clean:
		rm -f $(TARGETS)

templates/%.json: src/%.py
	python $< > $@

templates/%.json: src/%/
	python $< > $@