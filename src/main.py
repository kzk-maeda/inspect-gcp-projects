import csv
import json
import subprocess
from typing import List
from google.cloud import resource_manager


client = resource_manager.Client()


def get_iam_policy(project_id: str) -> List:
  command = ['gcloud', 'projects', 'get-iam-policy', project_id, '--format', 'json']
  try:
    res = subprocess.check_output(command)
  except Exception as e:
    print(e)
    return []
  dict_res = json.loads(res.decode('utf-8'))
  
  return dict_res.get('bindings')


def flatten_users(users: List) -> str:
  result_str = ""
  for user in users:
    user_name = user.split(':')[1]
    result_str = result_str + user_name + '\n'
  
  return result_str.rstrip("\n")


def get_services_list(project_id: str) -> List:
  command = ['gcloud', 'services', 'list', '--project', project_id, '--format', 'json']
  try:
    res = subprocess.check_output(command)
  except Exception as e:
    print(e)
    return []
  services = json.loads(res.decode('utf-8'))

  res_list = []
  for service in services:
    res = {
      'name': service.get('config').get('name'),
      'title': service.get('config').get('title')
    }
    res_list.append(res)

  return res_list


def flatten_services(services: List) -> str:
  result_str = ""
  for service in services:
    service_title = service.get('title')
    result_str = result_str + service_title + '\n'

  return result_str.rstrip("\n")


def write_csv(result_list: List) -> None:
  with open('gcp_projects.csv', 'w') as fw:
    writer = csv.DictWriter(fw, ['id', 'number', 'name', 'parent', 'status', 'owner', 'editor', 'viewer', 'other', 'services'])
    writer.writeheader()
    for result in result_list:
      writer.writerow(result)

  return


if __name__ == '__main__':
  count = 0
  result_list = []

  for project in client.list_projects():
    # 初期化
    count += 1
    result_row = {}
    # TODO: parentを分割
    result_row = {
      'id': project.project_id,
      'number': project.number,
      'name': project.name,
      'parent': project.parent,
      'status': project.status
    }
    iam_policy = get_iam_policy(project.project_id)
    # roleごとに抽出
    for member in iam_policy:
      if member.get('role') == 'roles/owner':
        result_row['owner'] = flatten_users(member.get('members'))
      elif member.get('role') == 'roles/editor':
        result_row['editor'] = flatten_users(member.get('members'))
      elif member.get('role') == 'roles/viewer':
        result_row['viewer'] = flatten_users(member.get('members'))
      else:
        result_row['other'] = flatten_users(member.get('members'))
    
    service_list = get_services_list(project.project_id)
    result_row['services'] = flatten_services(service_list)
    
    print(result_row)
    result_list.append(result_row)

    
  print(count)
  print(result_list)
  write_csv(result_list)
