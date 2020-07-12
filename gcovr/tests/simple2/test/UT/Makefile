all:
	$(CXX) -fprofile-arcs -ftest-coverage -fPIC ../../src/main.cpp -o testcase

run: txt xml html sonarqube json

txt:
	./testcase
	$(GCOVR) -r ../../src --keep -o ../../coverage.txt .

xml:
	./testcase
	$(GCOVR) -r ../../src --keep --xml --xml-pretty -o ../../coverage.xml .

html:
	./testcase
	$(GCOVR) -r ../../src --keep --html --html-details -o ../../coverage.html .

sonarqube:
	./testcase
	$(GCOVR) -r ../../src --keep --sonarqube ../../sonarqube.xml .

json:
	./testcase
	$(GCOVR) -r ../../src --keep --json ../../coverage.json .

clean:
	rm -f testcase
	rm -f *.gc* ../../src/*.gc*
	rm -f ../../coverage.txt ../../coverage.xml ../../coverage*.html ../../coverage*.css ../../sonarqube.xml ../../coverage.json
