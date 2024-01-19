import csv
import os
import statistics
from collections import defaultdict, namedtuple


# Tuple that represents a single point of data. Useful for extracting
# data from the experiment files.
DataPoint = namedtuple("DataPoint", ['participant', 'question', 'condition', 'words', 'reading_time', 'answer', 'answering_time'])


def collect_participant_times(csv_files, outfile="participant_times.csv"):
	""" Collects the average time per participant for answering to a
	question.
	
	Parameters
	----------
	csv_files : list(str)
		List of files that will be analysed.
	outfile : str
		File where the output will be written
	"""
	
	reaction_times = defaultdict(list)
	for source in csv_files:
		with open(source, 'r', encoding='utf-8-sig') as fp:
			reader = csv.DictReader(fp)
			for record in reader:
				participant = record['Participant Private ID']
				if record['Zone Type'] == 'continue_button':
					try:
						reaction = round(float(record['Reaction Time']))
						reaction_times[participant].append(reaction)
					except ValueError:
						assert record['Trial Number'] == 'BEGIN TASK', f"Missing value found ({record})"
					except TypeError:
						print(record)
						assert record['Event Index'] == 'END OF FILE', "Unexpected None value found"
	with open(outfile, "w") as fp:
		writer = csv.DictWriter(fp, fieldnames=['participant', 'q1', 'q2', 'q3', 'q4', 'q5', 'q6'])
		writer.writeheader()
		for participant, times in reaction_times.items():
			values = {'participant': participant,
					  'q1': times[0],
					  'q2': times[1],
					  'q3': times[2],
					  'q4': times[3],
					  'q5': times[4],
					  'q6': times[5]}
			writer.writerow(values)

def collect_item_reading_times(csv_files, outfile="all_reading_times.csv"):
	collected_data = []
	participants = set()
	for source in csv_files:
		with open(source, 'r', encoding='utf-8-sig') as fp:
			reader = csv.DictReader(fp)
			reading_time = []
			answer = -1
			for record in reader:				
				if record['Zone Name'] == 'spr':
					# We add more and more times to our list
					recorded_time = round(float(record['Reaction Time']))
					reading_time.append(recorded_time)
				elif record['Zone Type'] == 'response_slider_endValue':
					answer = int(record['Response']) 
				elif record['Zone Name'] == 'continueButton':
					# End of a question, we can complete now a record
					participant = record['Participant Private ID']
					question = record['stimulus_id'][:-2]
					condition = record['stimulus_id'][-1]
					words = len(record['sentence'].split(' '))
					answer_time = round(float(record['Reaction Time']))
					data_point = DataPoint(participant, question, 
										   condition, words, 
										   sum(reading_time), answer, 
										   answer_time)
					collected_data.append(data_point)
					participants.add(participant)
					# Reset the question_time variable for the next
					# question
					reading_time = []
					answer = -1
	with open(outfile, "w") as fp:
		csv_fields = ['participant', 'item_number', 'condition', 'words', 
					  'reading_time', 'answer', 'answering_time']
		writer = csv.DictWriter(fp, fieldnames=csv_fields)
		writer.writeheader()
		for record in collected_data:
			writer.writerow({'participant': record.participant,
							 'item_number': record.question,
							 'condition': record.condition,
							 'words': record.words,
							 'reading_time': record.reading_time,
							 'answer': record.answer,
							 'answering_time': record.answering_time})

def collect_data_stats(csv_files):
	collected_data = []
	participants = set()
	for source in csv_files:
		with open(source, 'r', encoding='utf-8-sig') as fp:
			reader = csv.DictReader(fp)
			reading_time = []
			answer = -1
			for record in reader:				
				if record['Zone Name'] == 'spr':
					# We add more and more times to our list
					recorded_time = round(float(record['Reaction Time']))
					reading_time.append(recorded_time)
				elif record['Zone Type'] == 'response_slider_endValue':
					answer = int(record['Response']) 
				elif record['Zone Name'] == 'continueButton':
					# End of a question, we can complete now a record
					participant = record['Participant Private ID']
					question = record['stimulus_id'][:-2]
					condition = record['stimulus_id'][-1]
					words = len(record['sentence'].split(' '))
					answer_time = round(float(record['Reaction Time']))
					data_point = DataPoint(participant, question, 
										   condition, words, 
										   sum(reading_time), answer, 
										   answer_time)
					collected_data.append(data_point)
					participants.add(participant)
					# Reset the question_time variable for the next
					# question
					reading_time = []
					answer = -1

	# Print some measures of interest
	avg_reading_time_per_condition = defaultdict(set)
	avg_reading_time_per_question = defaultdict(set)
	avg_reading_time_per_question_cond = defaultdict(set)
	scores_per_participant_a = defaultdict(list)
	scores_per_participant_b = defaultdict(list)
	reading_time_participant = defaultdict(int)
	answer_time_participant = defaultdict(int)
	collected_data.sort(key=lambda x: (x.question, x.condition))
	for record in collected_data:
		avg_reading_time_per_condition[record.condition].add(record.reading_time)
		avg_reading_time_per_question[record.question].add(record.reading_time)
		avg_reading_time_per_question_cond[record.question + '_' + record.condition].add(record.reading_time/record.words)
		if record.condition == 'a':
			scores_per_participant_a[record.participant].append(record.answer)
		else:
			scores_per_participant_b[record.participant].append(record.answer)
		reading_time_participant[record.participant] += record.reading_time/words
		answer_time_participant[record.participant] += record.answering_time
	"""
	print("Average reading time per condition")
	for condition, values in avg_reading_time_per_condition.items():
		print(f"  * {condition}: {sum(values)/len(values):.2f}")
	print("Average reading time per question")
	for condition, values in avg_reading_time_per_question.items():
		print(f"  * {condition}: {sum(values)/len(values):.2f}")
	print("Average reading time per question and condition")
	for condition, values in avg_reading_time_per_question_cond.items():
		print(f"  * {condition}: {sum(values)/len(values):.2f}")
	"""
	for participant in participants:
		single_reading_time = reading_time_participant[participant]
		single_answer_time = answer_time_participant[participant]
		print(f"{participant}: {single_reading_time:.02f} {single_answer_time:.02f}")
		answers_a = scores_per_participant_a[participant]
		answers_a.sort()
		print(f"  * {participant}: {answers_a} ({statistics.mean(answers_a):.2f})")
		answers_b = scores_per_participant_b[participant]
		answers_b.sort()
		print(f"  * {participant}: {answers_b} ({statistics.mean(answers_b):.2f})")

if __name__ == '__main__':
	# We only analyze the data for these specific tasks. Others, such
	# as "instructions", are not interesting for this script.
	interesting_tasks = {'25gc', '275q', '4d13', '4qbu', 
						 '94tq', '9zp6', 'ah8j', 'ty1q'}
	csv_files = []
	data_dir = 'data'
	for filename in os.listdir(data_dir):
		full_name = os.path.join(data_dir, filename)
		if os.path.isfile(full_name) and full_name.endswith('csv'):
			task_id = full_name[-8:-4]
			if task_id in interesting_tasks:
				csv_files.append(full_name)
	#collect_participant_times(csv_files)
	collect_item_reading_times(csv_files)
