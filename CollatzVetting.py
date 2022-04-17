import os
import glob
import json
import subprocess
import time

# must be absolute path; assuming running in Git Bash on Windows
# make sure to run after `make clean`
base_path = 'D:/Libraries Type-D/Documents/SCHOOL/UT Austin/Spring 2022/CS 330E Elements of Software Engineering (TA)/Projects/cs330e-collatz-grading-script'
output_path = base_path + '/output'
required_files = ['makefile', 'Collatz.py', 'RunCollatz.py', 'RunCollatz.in', 'RunCollatz.out', 'TestCollatz.py', 'TestCollatz.out', 'Collatz.html', 'Collatz.log']
optional_file = 'SphereCollatz.py'

def chdir(new_dir):
	try:
		os.chdir(new_dir)
		print('cd to ' + os.getcwd())
	except Exception as e:
		print('cd to ' + new_dir + ' failed. Exception message:\n')
		print(e)

submissions = {}
emails = {}
submissions_path = 'submissions/*.json'

# first, cd to the base_path and make all the directories needed; assuming that
# `submissions` directory is in the root of the base_path, and that `repos` and `output`
# do not exist.
chdir(base_path)
os.makedirs('repos')
os.makedirs('output')

# clone all gitlab repos
for filename in glob.glob(submissions_path):
	print("dealing with this filename: " + filename)
	with open(filename, 'r') as f:
		try:
			data = json.load(f)['Project #1']
			gitlab_username = data['GitLab Username']
			emails[gitlab_username] = {
				'email_1': data['Member #1 E-mail'],
				'email_2': data['Member #2 E-mail'],
				'eid_1': data['Member #1 EID'].lower(),
				'eid_2': data['Member #2 EID'].lower(),
				'contents': ''
			}
		except Exception as e:
			print('Invalid json for ' + filename)
			with open(output_path + '/invalidJson.txt', 'a') as f:
				f.write(filename + ' is invalid json\n' + str(e) + '\n\n')
			continue
		
		# construct the `.git` string from the GitLab URL; if any part failed,
		# try directly cloning from the provided username's namespace
		chdir('repos')
		
		try:
			gitlab_url = data['GitLab URL']
			clone_url = gitlab_url.replace('https://gitlab.com/', 'git@gitlab.com:').replace('http://gitlab.com/', 'git@gitlab.com:')
			if clone_url[-1] == '/':
				clone_url = clone_url[:-1]
			if clone_url[-4:] != '.git':
				clone_url += '.git'
			subprocess.check_call(['git', 'clone', clone_url, gitlab_username])
		except:
			try:
				clone_url = 'git@gitlab.com:' + gitlab_username + '/collatz.git'
				subprocess.check_call(['git', 'clone', clone_url, gitlab_username])
			except Exception as e:
				if 'already exists' not in str(e): 
					emails[gitlab_username]['contents'] += 'Repo ' + clone_url + ' not found\n'
		
		submissions[gitlab_username] = data
		chdir('..')

gitlab_usernames = submissions.keys()

# load our "answer key" for the acceptance tests
with open(base_path + '/RunCollatz.out') as file:
    collatzAnswerKey = file.read().splitlines()

numAcceptanceTests = len(collatzAnswerKey)

# HELPER FUNCTIONS START HERE
# =======================================================

# check git SHA; operates inside the `/repos/gitlab_username` folder
def check_SHA(gitlab_username):
	data = submissions[gitlab_username]
	print('Checking Git SHA for ' + os.getcwd())
	sha = str(subprocess.check_output(['git', 'rev-parse', 'HEAD']).strip(), 'utf-8')
	submitted_sha = data['Git SHA']
	if sha != submitted_sha:
		print('Submitted Git SHA does not match repo SHA')
		emails[gitlab_username]['contents'] += 'Submitted SHA in json does not match repo SHA\n'

# check all required files are present in repo
def check_required_files(gitlab_username):
	print('Checking files for ' + gitlab_username)
	numNotFound = 0
	for item in required_files:
		if item not in glob.glob(item):
			numNotFound += 1
			notFoundMessage = item + ' not found in repo\n'
			print(notFoundMessage)
			emails[gitlab_username]['contents'] += notFoundMessage
	if numNotFound > len(required_files) / 2:
		emails[gitlab_username]['contents'] += '(more than half of the required files are not found; are they in the root directory?)\n'
	if optional_file in glob.glob(optional_file):
		print('SphereCollatz.py found')
		with open(output_path + '/sphereList.txt', 'a') as f:
			f.write(gitlab_username + ' has SphereCollatz.py\n')
			
# examine unit tests
def checkUnitTests(gitlab_username):
	print('Checking unit tests for ' + gitlab_username)
	if 'makefile' not in glob.glob('makefile'):
		return
	if 'TestCollatz.py' not in glob.glob('TestCollatz.py'):
		return

	# run unit tests
	subprocess.call(['make', 'clean'])
	try:
		subprocess.call(['make', 'TestCollatz.tmp'])
	except:
		emails[gitlab_username]['contents'] += 'Unit tests failed\n'

	# count number of tests
	with open('TestCollatz.py','r') as f:
		num_tests = f.read().count('def test')
	with open('Collatz.py','r') as f:
		num_funcs = f.read().count('def ')
	print(str(num_tests) + ' tests and ' + str(num_funcs) + ' functions')
	if num_tests < num_funcs*3:
		emails[gitlab_username]['contents'] += 'Insufficient unit tests, ' + str(num_tests) + ' tests and ' + str(num_funcs) + ' functions\n'
			
# check acceptance tests: 
# 1. has to be >= 100 tests
# 2. runs successfully (does not error out or timeout on 150)
def checkAcceptanceTests(gitlab_username):
	print('Checking acceptance tests for ' + gitlab_username)
	if 'RunCollatz.in' not in glob.glob('RunCollatz.in'):
		return
	if 'RunCollatz.py' not in glob.glob('RunCollatz.py'):
		return
	
	# check to ensure that the file has at least 100 tests
	with open('RunCollatz.in', 'r') as f:
		numLines = len(f.readlines())
	if numLines < 100:
		emails[gitlab_username]['contents'] += 'Insufficient acceptance tests: only ' + str(numLines) + ' lines found.\n'
		
	# try running the acceptance test
	stdin = open('RunCollatz.in', 'r')
	stdout = open('RunCollatz.tmp', 'w')
	start_time = time.time()

	try:
		p = subprocess.Popen(['python', 'RunCollatz.py'], stdin=stdin, stdout=stdout)
		p.wait(timeout=150)
	except subprocess.TimeoutExpired as e:
		p.kill()
		p.communicate()
		print('Student Acceptance Tests Timeout')
		emails[gitlab_username]['contents'] += 'RunCollatz.in timed out on students\' acceptance tests (more than 150 seconds)\n'
	except Exception as e:
		emails[gitlab_username]['contents'] += 'Runtime Exception during students\' acceptance tests: ' + str(e) + '\n'
	print('Execution time (s): ' + str(time.time() - start_time))


# run our own Acceptance Test
def runOurAcceptanceTests(gitlab_username):
	print('Running our own acceptance tests for ' + gitlab_username)
	if 'RunCollatz.in' not in glob.glob('RunCollatz.in'):
		return
	if 'RunCollatz.py' not in glob.glob('RunCollatz.py'):
		return
		
	# try running the acceptance test
	stdin = open(base_path + '/RunCollatz.in', 'r')
	start_time = time.time()
	
	try:
		p = subprocess.Popen(['python', 'RunCollatz.py'], stdin=stdin, stdout=subprocess.PIPE)
		# p.wait(timeout=60)
		stdout, _ = p.communicate(timeout=60)
		
		# read the output into a variable directly
		collatzOutput = stdout.decode('cp437').splitlines()
		
		numFailedAcceptanceTests = 0
		for i in range(numAcceptanceTests):
			if collatzOutput[i] != collatzAnswerKey[i]:
				# print('mismatch!!! Index is: ' + str(i))
				# print(repr(collatzOutput[i]))
				# print(repr(collatzAnswerKey[i]))
				numFailedAcceptanceTests += 1
		
		if numFailedAcceptanceTests > 0:
			emails[gitlab_username]['contents'] += 'Number of Graders\' acceptance tests failed: ' + str(numFailedAcceptanceTests) + '\n'
	except subprocess.TimeoutExpired as e:
		p.kill()
		p.communicate()
		print('Grader Acceptance Tests Timeout')
		emails[gitlab_username]['contents'] += 'RunCollatz.in timed out on the graders\' acceptance tests (more than 60 seconds)\n'
	except Exception as e:
		emails[gitlab_username]['contents'] += 'Runtime Exception during graders\' acceptance tests: ' + str(e) + '\n'
	print('Execution time (s): ' + str(time.time() - start_time))


# HELPER FUNCTIONS END HERE
# =======================================================

# perform all the checks of the code repos (SHA and required files)
chdir(base_path + '/repos')
for gitlab_username in gitlab_usernames:
	# first try to get into the submission; skip if it doesn't exist
	try:
		os.chdir(gitlab_username)
		print('cd to ' + os.getcwd())
	except:
		print('failed to enter this GitLab ID folder: ' + gitlab_username)
		chdir(base_path + '/repos')
		continue
	
	check_SHA(gitlab_username)
	check_required_files(gitlab_username)
	checkUnitTests(gitlab_username)
	checkAcceptanceTests(gitlab_username)
	runOurAcceptanceTests(gitlab_username)
	
	chdir(base_path + '/repos')

# check required files are in the test repo
chdir(base_path)
subprocess.call(['git', 'clone', 'git@gitlab.com:fareszf/cs330e-collatz-tests.git'])
chdir('cs330e-collatz-tests')
existing_filenames = list(map(lambda filename: filename.lower(), os.listdir()))

for gitlab_username in gitlab_usernames:
	print('Checking test repo files for ' + gitlab_username)
	filenames = [
		gitlab_username + '-RunCollatz.in',
		gitlab_username + '-RunCollatz.out',
		gitlab_username + '-TestCollatz.py',
		gitlab_username + '-TestCollatz.out'
	]
	for filename in filenames:
		if filename.lower() not in existing_filenames:
			print(filename + ' not found in test repo')
			emails[gitlab_username]['contents'] += filename + ' missing in test repo\n'
		
# print out emails and resubmit requests
chdir(output_path)
for email in emails.values():
	if email['contents'] == '':
		continue
	with open('resubmitRequests.txt', 'a') as r:
		r.write(email['eid_1'] + ' and ' + email['eid_2'] + ' requested to resubmit\n')
	with open('email_output.txt', 'a') as o:
		o.write(email['email_1'] + '; ' + email['email_2'] + '\n')
		o.write('Hello,\n\nYou had the following errors in your Collatz submission:\n' + email['contents'] + '\nPlease resubmit within 24 hours for a 20% late penalty and message/email me when you have resubmitted.\n\nThanks,\nPeter\n\n')

chdir(base_path)

