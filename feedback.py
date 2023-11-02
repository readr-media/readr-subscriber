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


def valid_results_value(results: list, field_id: str) -> bool:
    '''
        Query filed options to check if the results are valid.
    '''
    query = '''
        query FieldOptions($where: FieldOptionWhereInput!) {
            fieldOptions(where: $where) {
                id
            }
        }
    '''
    variables = {
        "where": {
            "field": {"id": {"equals": f"{field_id}"}},
            "value": {"in": [f"{result}" for result in results]}
        }
    }

    result = gql_client.execute(gql(query), variable_values=variables)
    return len(result['fieldOptions']) == len(results)


def create_formResult(gql_client, name, ip, result, responseTime, form, field, uri):
  mutation_data = '''
        data: {
          %s
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
      ''' %(uri, name, ip, result, responseTime, form, field)
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


def delete_name_uri_exist_result(gql_client, name, fieldId, uri):
  query = '''query{
    formResults(where:{name:{in:"%s"} ,field:{id:{in:%s}}, uri:{equals:"%s"}} orderBy:{name:desc}){
      id
    }
  }
''' %(name, fieldId, uri)
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


def query_form_result(gql_client, name, field_id, uri):
    # Query "formResults" instead of single "formResult" is because the current "formResult" query schema
    # only allow "id" as the query variable.
    # Might need to refactor it someday.
    query = '''
        query FormResults($where: FormResultWhereInput!) {
            formResults(where: $where, orderBy:{createdAt:desc}) {
                id
            }
        }
    '''
    variables = {
        "where": {
            "name": {"equals": f"{name}"},
            "field": {"id": {"equals": f"{field_id}"}},
            "uri": {"equals": f"{uri}"},
        }
    }
    result = gql_client.execute(gql(query), variable_values=variables)
    return result['formResults']


def update_form_result(gql_client, form_result_id, result, response_time):
    mutation = '''
        mutation UpdateFormResult($where: FormResultWhereUniqueInput!, $data: FormResultUpdateInput!) {
            updateFormResult(where: $where, data: $data) {
                id
            }
        }
    '''
    variables = {
        "where": {"id": f"{form_result_id}"},
        "data": {
            "result": f"{result}",
            "responseTime": f"{response_time}"
        }
    }
    result = gql_client.execute(gql(mutation), variable_values=variables)
    if result['updateFormResult'].get('id', '') != form_result_id:
       return False
    return True


def delete_single_form_result(gql_client, form_result_id):
    mutation = '''mutation{
        deleteFormResult(where:{id:%s}){
            id
        }
    }'''% form_result_id
    result = gql_client.execute(gql(mutation))
    if result['deleteFormResult'].get('id', '') != form_result_id:
        return False
    return True

def delete_multiple_form_result(gql_client, form_result_id_list):
    mutation = '''
        mutation($where: [FormResultWhereUniqueInput!]!){
            deleteFormResults(where: $where){
                id
            }
       }
    '''

    variables = {
       "where": list(map(lambda form_result_id: { id: form_result_id}, form_result_id_list))
    }
    result = gql_client.execute(gql(mutation), variable_values=variables)
    return True
      

def feedback_handler(data):
    name = data['name']
    form = data['form']
    field = data['field']
    result = data['userFeedback'].lower()
    ip = data['ip']
    responseTime = data['responseTime']
    if 'uri' in data:
        uri = data['uri']
        uri_script = f'uri: "{uri}",'
    else:
        uri = ''
        uri_script = ''
    # ip_regex = re.compile(r'[0-9]+[.][0-9]+[.][0-9]+[.][0-9]+')
    # if not re.fullmatch(ip_regex, ip) :
    #   print("ip format not match.")
    #   return False
    responseTime_regex = re.compile(r'20[0-9][0-9]-(0?[1-9]|1[0-2])-(0?[1-9]|[12]\d|30|31)T([01][0-9]|2[0-3]):([0-5][0-9]|60):([0-5][0-9]|60).([0-9][0-9][0-9])Z')
    if not re.fullmatch(responseTime_regex, responseTime) :
        print("responseTime format not match.")
        return False

    field_type = query_filedtype(gql_client, field)
    if field_type == 'text':
        return create_formResult(gql_client, name, ip, result, responseTime, form, field, uri_script)
    elif field_type in {'single', 'multiple'}:
        form_results = query_form_result(gql_client, name, field, uri)
        
        results = result.split("$$")
        if len(form_results) == 0:
            if not valid_results_value(results, field):   
                print(f"Invalid userFeedback '{result}' on field id '{field}'")
                return False
            return create_formResult(gql_client, name, ip, result, responseTime, form, field, uri_script)
        else:
            if len(form_results) > 1:
              print(f"There are more than one form result, got {form_results}")

            if result == "":
               form_result_id_list = list(map(lambda result: result['id'], form_results))
               return delete_multiple_form_result(gql_client, form_result_id_list)
            if not valid_results_value(results, field):
                print(f"Invalid userFeedback '{result}' on field id '{field}'")
                return False
            
            form_result_id = form_results[0]['id']
            return update_form_result(gql_client, form_result_id, result, responseTime)
    elif field_type == 'checkbox':
        # TODO: Might implement it in the future.
        return False
    else:
        return False


if __name__ == '__main__':

  from datetime import datetime
  today = datetime.now()
  iso_date = today.isoformat()[:-3]
  data_comment = {
  "name": "uuid",
  "form": "2",
  "ip": "2.1.1.22",
  # "responseTime": '2022-11-11T05:00:00.000Z',
  "responseTime": iso_date+'Z',
  "field": "6", 
  "userFeedback": "true",
  "uri": "https://www.google.com"
  }
  print(feedback_handler(data_comment))
