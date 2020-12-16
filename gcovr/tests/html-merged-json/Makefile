all:
	$(CXX) -fprofile-arcs -ftest-coverage -fPIC main.c -o testcase
	cd subdir ; $(CXX) -fprofile-arcs -ftest-coverage -fPIC unit.c -o testcase

run: html

coverage.json:
	./testcase
	$(GCOVR) -d --json main.json
	./subdir/testcase
	$(GCOVR) -d --json unit.json subdir
	$(GCOVR) --add-tracefile main.json --add-tracefile unit.json --json $@

html: coverage.json
	$(GCOVR) --add-tracefile $< --html-details -o coverage.html

clean:
	rm -f testcase subdir/testcase main.json unit.json
	rm -f *.gc*
	rm -f coverage.json coverage*.html coverage.css
