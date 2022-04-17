import os
import glob
import json
import subprocess
import time

# `base_path` must be absolute path; assuming running in Git Bash on Windows
# make sure to run after `make clean`
base_path = 'D:/Libraries Type-D/Documents/SCHOOL/UT Austin/Spring 2022/CS 330E Elements of Software Engineering (TA)/Projects/cs330e-collatz-grading-script'
output_path = 'output'
output_filename = 'bad_cooperation_list.txt'
submissions_path = 'evaluation_submissions/*.json'

def chdir(new_dir):
	try:
		os.chdir(new_dir)
		print('cd to ' + os.getcwd())
	except Exception as e:
		print('cd to ' + new_dir + ' failed. Exception message:\n')
		print(e)

submissions = {}
output_string = ''
submissions_path = 'evaluation_submissions/*.json'

# first, cd to the base_path and make the directory if necessary
chdir(base_path)
if not os.path.exists(output_path):
	os.makedirs(output_path)

# clone all gitlab repos
for filename in glob.glob(submissions_path):
	# print("dealing with this filename: " + filename)
	with open(filename, 'r') as f:
		try:
			data = json.load(f)['Project #1']
			# only proceed if the cooperation points assignment is not the maximum
			assigned_points = data['Member #2 Cooperation Points']
			if assigned_points == 20:
				continue
			
			eid = data['EID']
			current_student_name = data['First Name'] + ' ' + data['Last Name']
			target_student_name = data['Member #2 First Name'] + ' ' + data['Member #2 Last Name']
			
		except Exception as e:
			print('Invalid json for ' + filename)
			with open(output_path + '/invalidEvaluationJson.txt', 'a') as f:
				f.write(filename + ' is invalid json\n' + str(e) + '\n\n')
			continue
		
		output_string += f'{current_student_name} only assigned {assigned_points} points to {target_student_name}!\n'
		

# print out emails and resubmit requests
chdir(output_path)
with open(output_filename, 'w') as output_file:
	output_file.write(output_string)

chdir(base_path)

