all: clean vetting bad_cooperation_list

clean:
	rm -rf cs330e-collatz-tests
	rm -rf repos
	rm -rf output

vetting:
	python CollatzVetting.py
	
bad_cooperation_list:
	python CollatzCheckCooperationPoints.py