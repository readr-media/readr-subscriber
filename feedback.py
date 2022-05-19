import os
import re
from uuid import uuid4
from gql import gql, Client
from gql.transport.aiohttp import AIOHTTPTransport


gql_endpoint = os.environ['GQL_ENDPOINT']
gql_transport = AIOHTTPTransport(url=gql_endpoint)
gql_client = Client(transport=gql_transport, fetch_schema_from_transport=True)
def create_feedback(data):
  create_result = []
  name = str(uuid4())
  form = data['form']
  ip = data['ip']
  ip_regex = re.compile(r'[0-9]+[.][0-9]+[.][0-9]+[.][0-9]+')
  if not re.fullmatch(ip_regex, ip) :
    print("ip format not match.")
    return False
  responseTime = data['responseTime']
  responseTime_regex = re.compile(r'20[0-9][0-9]-(0?[1-9]|1[0-2])-(0?[1-9]|[12]\d|30|31)T([01][0-9]|2[0-3]):([0-5][0-9]|60):([0-5][0-9]|60).([0-9][0-9][0-9])Z')
  if not re.fullmatch(responseTime_regex, responseTime) :
    print("responseTime format not match.")
    return False
  for result in data['result']:
    field = result['field']
    result = result['userFeedback']
    mutation_data = '''
      data: {
        name: "%s",
        ip: "%s",
        result: "%s",
        responseTime: "%s",
        form: {
          connect: {
            id: "%s"
          }
        },
        field: {
          connect: {
            id: "%s"
          }
        }
      }
    ''' %(name, ip, result, responseTime, form, field)
    mutation = '''
    mutation{
      createFormResult(%s){
        id
      }
    }
    ''' % mutation_data
    print(mutation)
    result = gql_client.execute(gql(mutation))
    print(result)
    if not isinstance(result, dict) and 'createFormResult' not in result:
      print(result)
      return False
    if isinstance(result['createFormResult'], dict) and 'id' in result['createFormResult']:
      create_result.append(result['createFormResult']['id'])
    else: 
      print(result)
      return False
  return True
if __name__ == '__main__':
  data = {"form": "2",
  "ip": "2.1.1.22",
  "responseTime": '2022-05-19T05:00:00.000Z',
  "result": [
      {"field": "6", "userFeedback": "不符合"},
      {"field": "7", "userFeedback": "巴拉巴拉使用者的實際經驗～～"},
]}
  print(create_feedback(data))