.PHONY: all clean
all:
	mkdir -p build output
	latexmk -pdf -interaction=nonstopmode -halt-on-error -outdir=build -jobname=paper_1167 main.tex
	cp build/paper_1167.pdf output/paper_1167.pdf

clean:
	rm -rf build
