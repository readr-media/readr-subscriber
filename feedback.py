import os
import re

from gql import gql, Client
from gql.transport.aiohttp import AIOHTTPTransport


gql_endpoint = os.environ['GQL_ENDPOINT']


gql_transport = AIOHTTPTransport(url=gql_endpoint)
gql_client = Client(transport=gql_transport, fetch_schema_from_transport=True)
def query_filedtype(gql_client, filedId):
  query = '''
  query{
  field(where:{id:%s}){
    type
    }
  }
    '''%filedId
  query_result = gql_client.execute(gql(query))
  if isinstance(query_result, dict) and 'field' in query_result:
    if query_result['field']:
      type = query_result['field']['type']
      return type
    else:
      print(f"filedId {filedId} not found")
      return False
  else:
    return False

def create_formResult(gql_client, name, ip, result, responseTime, form, field):
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
  createFormResult = '''
    mutation{
      createFormResult(%s){
        id
      }
    }
    ''' % mutation_data
  print(createFormResult)
  mutation_result = gql_client.execute(gql(createFormResult))
  if not isinstance(mutation_result, dict) and 'createFormResult' not in mutation_result:
    print(mutation_result)
    return False
  if isinstance(mutation_result['createFormResult'], dict) and 'id' in mutation_result['createFormResult']:
    return True
  else: 
    print(mutation_result)
    return False
def delete_name_exist_result(gql_client, name, fieldId):
  query = '''query{
    formResults(where:{name:{in:"%s"} ,field:{id:{in:%s}}} orderBy:{name:desc}){
      id
    }
  }
''' %(name, fieldId)
  print(query)
  query_result = gql_client.execute(gql(query))
  if isinstance(query_result, dict) and 'formResults' in query_result:
    if query_result['formResults']:
      #the user's feed-like result in formResults
      id = query_result['formResults'][0]['id']
      deleteFormResult = '''
      mutation{
          deleteFormResult(where:{id:%s}){
            id
          }
        }'''% id
      print(deleteFormResult)
      mutation_result = gql_client.execute(gql(deleteFormResult))
      if not isinstance(mutation_result, dict) and 'deleteFormResult' not in mutation_result:
        print(mutation_result)
        print("deleteFormResult fail")
        return False
      if isinstance(mutation_result['deleteFormResult'], dict) and 'id' in mutation_result['deleteFormResult']:
        return True
      else: 
        print(mutation_result)
        print("deleteFormResult fail")
        return False


    else:
      #user feed-like result not in formResults
      return True
      

def feedback_handler(data):
  name = data['name']
  form = data['form']
  field = data['field']
  result = data['userFeedback'].lower()
  ip = data['ip']
  responseTime = data['responseTime']

  # ip_regex = re.compile(r'[0-9]+[.][0-9]+[.][0-9]+[.][0-9]+')
  # if not re.fullmatch(ip_regex, ip) :
  #   print("ip format not match.")
  #   return False
  responseTime_regex = re.compile(r'20[0-9][0-9]-(0?[1-9]|1[0-2])-(0?[1-9]|[12]\d|30|31)T([01][0-9]|2[0-3]):([0-5][0-9]|60):([0-5][0-9]|60).([0-9][0-9][0-9])Z')
  if not re.fullmatch(responseTime_regex, responseTime) :
    print("responseTime format not match.")
    return False

  field_type = query_filedtype(gql_client, field)
  if field_type:
    if field_type=='text':
      return create_formResult(gql_client, name, ip, result, responseTime, form, field)
    elif field_type=='single':
      if delete_name_exist_result(gql_client, name, field) is False:
        return False
      if result == 'true' or result == 'false':
        return create_formResult(gql_client, name, ip, result, responseTime, form, field) 
      else: 
        return True
    else:
      return False
  else:
    return False


if __name__ == '__main__':

  data_comment = {
  "name": "uuid",
  "form": "3",
  "ip": "2.1.1.22",
  "responseTime": '2022-05-19T05:00:00.000Z',
  "field": "7", 
  "userFeedback": "使用者的實際經驗感想",
  }
  print(feedback_handler(data_comment))
