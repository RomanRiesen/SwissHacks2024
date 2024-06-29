from openai import OpenAI

import requests
import traceback
import docker
import re
import pprint

# FIXME #FIXME #FIXME env variable

app_under_testing_path = "../postfinance/source"
yaml_path = app_under_testing_path + "/src/main/resources/openapi/openapi.yml"
requirements_path = app_under_testing_path + "/spec/Requirements.md"

# What are the chances gpt will understand this?
test_users = """\
| Username    | Password          | Role  |
|-------------|-------------------|-------|
| john.doe    | strong-password   | User  |
| jane.smith  | you-dont-guess-me | User  |
| jimmy.allen | secure-secret     | Admin |
"""


def test_idea_prompt():
    prompt = "You are a testing engineer focused on correctness. Write only a concise list as in the given example. You wish to test this user story for the above api. You only have access to the api not the code. Write a detailed list of automatable tests you would write to verify the api works. Think of further steps to verify the work is successful."
    context = [
        {
            "role": "user",
            "content": "Here is an openapi spec:\n"
            + open(yaml_path, "r").read()
            + "It has the following default users:\n"
            + test_users
            + prompt
            + """
            User Story 1: Customer Registration
            As a new customer, I want to register for an online banking account so that I can access banking services.

            - **Given** I am not registered to the online banking service
            - **When** I navigate to the bank's registration page
            - **And** submit my firstname, lastname and birthdate
            - **Then** I receive confirmation of successful registration in form of a username and password
            """,
        },
        {
            "role": "assistant",
            "content": """
Here is a detailed list of tests that can be performed to verify that the customer registration API works as expected:
1. Test that the API returns a 400 Bad Request status code when the request body is missing any of the required fields (first name, last name, date of birth).
2. Test that the API returns a 400 Bad Request status code when the first name or last name exceeds the maximum length of 32 characters.
3. Test that the API returns a 400 Bad Request status code when the date of birth is not in the correct format (yyyy-mm-dd).
4. Test that the API returns a 400 Bad Request status code when the date of birth is in the future.
5. Test that the API returns a 400 Bad Request status code when the date of birth indicates that the customer is under 18 years old.
6. Test that the API returns a 201 Created status code when the request body contains valid data.
7. Test that the response body includes a username and password when the registration is successful.
8. Test that the username is a combination of the first name and last name, separated by a dot.
9. Test that the password meets the password policy requirements (e.g., minimum length, character complexity).
10. Test that the API returns a 409 Conflict status code when attempting to register a customer with the same first name, last name, and date of birth as an existing customer.
11. Test that the API returns a 500 Internal Server Error status code when an unexpected error occurs during the registration process.
12. Test that the API properly handles special characters and non-ASCII characters in the request body.
13. Test that the API properly validates the date of birth to ensure the customer is of legal age to register for an online banking account.
14. Test that the API properly logs and/or alerts on failed registration attempts, such as repeated attempts to register with the same information or attempts to register with invalid input.
15. Test that the API properly stores the customer's information in a secure and encrypted manner, such as hashing the password and encrypting sensitive data.
16. Test that the API properly integrates with any necessary backend systems, such as a customer database or identity management system.
17. Test that the API properly handles concurrent registration requests from multiple users.
18. Test that the API properly handles registration requests from users with different roles, such as regular users and administrators.
19. Test that the API properly handles registration requests from users with different authorization levels, such as unauthenticated users and authenticated users.
20. Test that the API properly handles registration requests from users with different locales and languages.
""",
        },
        {
            "role": "user",
            # "content": "you, an experienced test engineer and business analyst wants to write tests for the following user story. Write a list of tests. Try to avoid false positives.:\n",
            "content": "Thank you that is exactly what i looked for! Now, onto a different user study.\n",
        },
        {
            "role": "user",
            # "content": "you, an experienced test engineer and business analyst wants to write tests for the following user story. Write a list of tests. Try to avoid false positives.:\n",
            "content": prompt,
        },
    ]
    print(context)
    return context


test1 = """
import requests
import json

def test_customer_registration_exceeds_max_length():
    # Set up the API endpoint and test data
    url = "http://localhost:8080/customers/register"
    headers = {"Content-Type": "application/json"}

    # Test first name exceeds max length
    data = json.dumps({
        "firstName": "a" * 33,
        "lastName": "Doe",
        "dateOfBirth": "1990-01-01"
    })
    response = requests.post(url, headers=headers, data=data)
    assert response.status_code == 400

    # Test last name exceeds max length
    data = json.dumps({
        "firstName": "John",
        "lastName": "a" * 33,
        "dateOfBirth": "1990-01-01"
    })
    response = requests.post(url, headers=headers, data=data)
    assert response.status_code == 400
"""


def remove_lines_until_first_function(code):
    # Find the index of the first function name
    function_name_index = re.search(r"def .*:", code).end()
    # Remove the lines up to the end of the first function name
    code = code[function_name_index:]
    # Un-indent the code
    # code = re.sub(r'^ {4}', '', code, flags=re.MULTILINE)
    code = (
        "ret = True\ntry: "
        + code
        + "except AssertionError as e: ret = traceback.format_exception(e)\n"
    )
    return code


tests = list(map(remove_lines_until_first_function, [test1]))


# TODO search common endpoints for yaml
def get_stories():
    with open(requirements_path, "r") as file:
        stories = file.read().split("\n## ")[1:]
        stories = [[y for y in x.split("\n### Scenario:") if y != ""] for x in stories]
        return stories


def split_test_ideas(test_ideas):
    return re.split(r"\d+\.", test_ideas)
    # return test_ideas


def send_to_gpt(prompt: str, top_p: float = 0.5, temperature: float = 0.7, context=""):
    client = OpenAI(api_key=OPENAI_KEY)
    response = client.chat.completions.create(
        model="gpt-4-turbo",
        top_p=top_p,
        temperature=temperature,
        messages=context + [{"role": "user", "content": prompt}],
    )
    return response.choices[0].message.content


def main():
    # for story in get_stories():
    #    s = "\n".join(story)
    #    test_ideas = send_to_gpt(
    #        s, context=test_idea_prompt(), top_p=0.3, temperature=0.1
    #    )
    #    print(test_ideas)
    test_ideas = send_to_gpt(
        "\n".join(get_stories()[1]),
        context=test_idea_prompt(),
        top_p=0.3,
        temperature=0.5,
    )

    test_ideas = split_test_ideas(test_ideas)

    for idea in test_ideas:
        pprint.pprint(idea)

    # pprint.pprint(test_ideas)


if __name__ == "__main__":
    main()
