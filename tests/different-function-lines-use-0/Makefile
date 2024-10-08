include $(dir $(MAKEFILE_LIST))../common.mk

all:
	mkdir -p build1 build2
	cd build1 ; $(CXX) $(CXXFLAGS) ../main.c -o testcase
	cd build2 ; $(CXX) $(CXXFLAGS) -DFOO_OTHER_LINE ../main.c -o testcase

run: txt lcov cobertura html sonarqube coveralls

coverage.json:
	cd build1 ; ./testcase
	cd build2 ; ./testcase
	$(GCOVR) --json-pretty --json coverage.json ; test $$? -eq 64
	$(GCOVR) --verbose --merge-mode-functions=merge-use-line-0 --json-pretty --json coverage.json

txt: coverage.json
	$(GCOVR) -a $< -o coverage.txt

lcov: coverage.json
	$(GCOVR) -a $< --lcov coverage.lcov

cobertura: coverage.json
	$(GCOVR) -a $< --cobertura-pretty --cobertura cobertura.xml

html: coverage.json
	$(GCOVR) -a $< --html-details -o coverage.html

coveralls: coverage.json
	$(GCOVR) -a $<  --coveralls-pretty --coveralls coveralls.json

sonarqube: coverage.json
	$(GCOVR) -a $< --sonarqube -o sonarqube.xml

clean:
	rm -rf build1 build2
	rm -f *.gc* coverage*.* cobertura*.* sonarqube*.* coveralls.json
