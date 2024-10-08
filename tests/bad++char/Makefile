include $(dir $(MAKEFILE_LIST))../common.mk

all:
	$(CXX) $(CXXFLAGS) main.cpp -o testcase

run: txt cobertura html sonarqube jacoco json_summary coveralls

coverage.json:
	./testcase
	$(GCOVR) --json-pretty --json coverage.json

txt: coverage.json
	$(GCOVR) -a $< -o coverage.txt

cobertura: coverage.json
	$(GCOVR) -a $< --cobertura-pretty --cobertura cobertura.xml

html: coverage.json
	$(GCOVR) -a $< --html-details -o coverage.html

sonarqube: coverage.json
	$(GCOVR) -a $< --sonarqube -o sonarqube.xml

jacoco: coverage.json
	$(GCOVR) -a $< --jacoco -o jacoco.xml

coveralls: coverage.json
	$(GCOVR) -a $< --coveralls-pretty --coveralls coveralls.json

json_summary:
	./testcase
	$(GCOVR) -d --json-summary-pretty -o summary_coverage.json

clean:
	rm -f testcase
	rm -f *.gc*
	rm -f coverage*.* cobertura*.* sonarqube*.* jacoco*.* summary_coverage.json coveralls.json
