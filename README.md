# Ansible Lab #5 - 헬스 스코어를 웹엑스로 전송 

<br><br>

## Lab 진행 순서  

<br>

1. Planybook (main.yml) 내용을 살펴봅니다.

```yaml
- hosts: aci
  connection: local
  gather_facts: no
  collections:
  - cisco.aci

  roles:
  - monitor_health
  - call_webex
```
- 데이터를 수집하는 태스크와 Webex로 메시지를 보내는 태스크를 별도의 Role로 분리되어 작성되어 있습니다.

<br><br>

2. roles/monitor_health/tasks/main.yml 파일을 살펴봅니다.

```yaml
- name: "시스템 헬스 정보 수집"
  aci_rest:
    ...
    path: /api/mo/topology/health.json
    method: get
  register: health_system

- name: "토폴로지 헬스 정보 수집"
  aci_rest:
    ...
    path: /api/node/class/topSystem.json?rsp-subtree-include=health,required&rsp-subtree-filter=le(healthInst.cur,"{{ item.score }}")
    method: get
  with_items: 
    - score: 100
  register: health_topology

- name: "각 테넌트 별 헬스 정보 수집"
  aci_rest:
    ...
    path: /api/node/class/fvTenant.json?rsp-subtree-include=health,required&rsp-subtree-filter=le(healthInst.cur,"{{ item.score }}")
    method: get
  with_items: 
    - score: 100
  register: health_tenant
```
- 헬스 스코어, 토폴로지 헬스 스코어, 테넌트 헬스 스코어를 수집합니다.
- 토폴로지 헬스 스코어와 테넌트 헬스 스코어는 특정 score 이하의 대상만을 수집합니다. 

<br>

```yaml
- name: "시스템/토폴로지/테넌트 헬스 정보를 Json 파일로 저장"
  copy:
    content: "{{ item.content | to_nice_json}}"
    dest:    "{{ item.dest }}"
  no_log: yes
  loop:
    - content: "{{ health_system }}"
      dest:    "roles/monitor_health/files/health_system.json"
    - content: "{{ health_topology }}"
      dest:    "roles/monitor_health/files/health_topology.json"
    - content: "{{ health_tenant }}"
      dest:    "roles/monitor_health/files/health_tenant.json"

- name: "메시지 전송 여부 체크 스크립트 실행"
  script: check.py
  register: check_result

- name: "수집한 데이터를 Webex 메시지 형태의 파일로 변환 (Markdown 포맷)"
  template: 
    src:  "template/health_report.j2"
    dest: "roles/call_webex/files/health_report.md"
  when: check_result.stdout | bool
```
- 각각의 헬스스코어를 Json 파일로 저장을 합니다.
- check.py 스크립트를 실행하여 저장된 Json을 읽고, 메시지 전송 여부를 결정합니다. 
- 전송할 메시지를 Webex 전송에 맞는 파일 형식으로 변환합니다.

<br><br>

3. roles/call_webex/tasks/main.yml 파일을 살펴봅니다.
```yaml
- name: "전송 파일 유무 확인"
  stat: path="roles/call_webex/files/health_report.md"
  register: file_check

- name: "전송할 파일 읽기"
  debug: msg="{{lookup('file', 'health_report.md') }}"
  register:   health_tenant_message
  when: file_check.stat.exists
  
- name: "Webex로 메시지 전송" 
  cisco_spark:
    recipient_type:   roomId
    recipient_id:     "{{ roomID }}"
    message_type:     markdown
    personal_token:   "{{ bot_token }}"
    message:          "{{ health_tenant_message.msg }}"
  when: file_check.stat.exists
```
- 전송할 메시지 파일이 있는 지를 체크합니다.
- 전송할 메시지 파일을 읽고, Webex로 전송합니다.

<br>

```yaml
- name: "전송된 파일 삭제"
  file:
    path: roles/call_webex/files/health_report.md
    state: absent
```
- 전송된 메시지 파일은 삭제합니다.

<br><br>

4. Playbook을 실행하여 결과를 확인합니다.
```
ansible-playbook -i hosts main.yml
```

<br><br>

5. roles/monitor_health/tasks/main.yml 파일에서 전송 기준 score를 수정합니다.
```yaml
- name: "토폴로지 헬스 정보 수집"
  aci_rest:
    ...
    path: /api/node/class/topSystem.json?rsp-subtree-include=health,required&rsp-subtree-filter=le(healthInst.cur,"{{ item.score }}")
    method: get
  with_items: 
    - score: 100
  register: health_topology

- name: "각 테넌트 별 헬스 정보 수집"
  aci_rest:
    ...
    path: /api/node/class/fvTenant.json?rsp-subtree-include=health,required&rsp-subtree-filter=le(healthInst.cur,"{{ item.score }}")
    method: get
  with_items: 
    - score: 100
  register: health_tenant
```
- score: 100을 더 낮은 점수로 변경하고, playbook을 실행합니다. 

<br><br>

6. Playbook을 실행하여 결과를 확인합니다.
```
ansible-playbook -i hosts main.yml
```