all: clean vetting

clean:
	rm -rf cs330e-collatz-tests
	rm -rf repos
	rm -rf output

vetting:
	python CollatzVetting.py