.PHONY: all
all:
	mkdir -p build output
	latexmk -pdf -interaction=nonstopmode -halt-on-error -outdir=build -jobname=manuscript_skeleton main.tex
	cp build/manuscript_skeleton.pdf output/manuscript_skeleton.pdf
