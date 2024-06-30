from openai import OpenAI

import requests
import traceback
import docker
import re
import sys
import os
import subprocess
from rich.columns import Columns
from rich import print as rprint
from rich.panel import Panel
from rich.console import Console
from rich.syntax import Syntax
from dataclasses import dataclass
from rich.markdown import Markdown
import pathlib

# FIXME #FIXME #FIXME env variable
OPENAI_KEY = os.environ["OPENAI_KEY"]

pwd = pathlib.Path(__file__).parent
app_under_testing_path = pwd / ".." / "postfinance" / "source"
yaml_path = (
    pathlib.Path(app_under_testing_path)
    / "src"
    / "main"
    / "resources"
    / "openapi"
    / "openapi.yml"
)
requirements_path = pathlib.Path(app_under_testing_path) / "spec" / "Requirements.md"

# What are the chances gpt will understand this?
test_users = """\
| Username    | Password          | Role  |
|-------------|-------------------|-------|
| john.doe    | strong-password   | User  |
| jane.smith  | you-dont-guess-me | User  |
| jimmy.allen | secure-secret     | Admin |
"""


def write_to_file(filename, mode="w"):
    def decorator(func):
        def wrapper(*args, **kwargs):
            if not os.path.exists(filename):
                with open(filename, mode) as f:
                    result = func(*args, **kwargs)
                    f.write(str(result))
                    return result
            else:
                with open(filename, "r") as f:
                    return f.read()

        return wrapper

    return decorator


@dataclass
class Persona:
    prompt = "You write clear and concise code that gives. "
    identifier: int


class CyberPersona(Persona):
    prompt = (
        Persona.prompt
        + "You are an experienced offensive cybersecurity engineer. You are specialized in API testing and know how to identify potential security gaps from the standard API specifications that you are provided. You have 20 plus years experience and are aware of historically security breaches in the past which you leverage to create your own test cases. You understand business requirements well, and you are able to make connections identifying unstated requirements necessary to be tested in an API for which a written specification is often not made as it would be too time consuming for a developer or overlooked because appears as common sense."
    )
    identifier = 1


class TesterPersona(Persona):
    prompt = (
        Persona.prompt
        + "You are a testing engineer focused on correctness. Write only a concise list as in the given example. You wish to test this user story for the above api. You only have access to the api not the code. Write a detailed list of automatable tests you would write to verify the api works. Think of further steps to verify the work is successful."
    )
    identifier = 2


class EdgeCasePersona(Persona):
    prompt = (
        Persona.prompt
        + "You are a Senior Engineer with a decade of experience. Your detail-oriented nature and gives you a knack for finding tricky edge cases."
    )
    identifier = 3


class HappyPathPersona(Persona):
    prompt = (
        Persona.prompt
        + "You are an expert software engineer and have a knack for writing clean, efficient code. You love verifying the happy path and do so with very readable code."
    )
    identifier = 4  # should've used hashes


def test_idea_prompt(persona: Persona):
    prompt = (
        persona.prompt
        + "Write only a concise list as in the given example. You wish to test this user story for the below api. You only have access to the api not the code. Write a detailed list of automatable tests you would write to verify the api works. Think of further steps to verify the work is successful."
    )
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
    return context


def python_test_prompt(persona: Persona):
    prompt = [
        {
            "role": "user",
            "content": "Here is the openapi spec, look at it carefully:\n"
            + open(yaml_path, "r").read()
            + "It has the following default users:\n"
            + test_users
            + persona.prompt
            + """
            Write a test in python for: Test that the API returns a 400 Bad Request status code when the first name or last name exceeds the maximum length of 32 characters.
""",
        },
        {
            "role": "assistant",
            "content": """
```
import requests
import string
import random

# Set up the API endpoint and test data
url = "http://localhost:8080/customers/register"

# Test first name exceeds max length
data = {
    "firstName": "a" * 33,
    "lastName": "Doe",
    "dateOfBirth": "1990-01-01"
}
response = requests.post(url, json=data)
assert response.status_code == 400

# Test last name exceeds max length
data = {
    "firstName": "John",
    "lastName": "a" * 33,
    "dateOfBirth": "1990-01-01"
}
response = requests.post(url, json=data)
assert response.status_code == 400

# Test excessively long input
data = {
    "firstName": "a" * 1000,
    "lastName": "Doe",
    "dateOfBirth": "1990-01-01"
}
response = requests.post(url, json=data)
assert response.status_code == 400

# Test special characters
data = {
    "firstName": "<script>alert('XSS')</script>",
    "lastName": "Doe",
    "dateOfBirth": "1990-01-01"
}
response = requests.post(url, json=data)
assert response.status_code == 400

# Test non-ASCII characters
data = {
    "firstName": "John".encode("utf-8").decode("utf-8"),
    "lastName": "Smith".encode("utf-8").decode("utf-8"),
    "dateOfBirth": "1990-01-01"
}
response = requests.post(url, json=data)
assert response.status_code == 201
```
"""
            + """You are an experienced developer. Do not annotate code in any way except for comments. Do not try to register users already registered (remember the user list). Write a python test as above for:""",
        },
    ]
    return prompt


# TODO search common endpoints for yaml
def get_stories():
    with open(requirements_path, "r") as file:
        stories = file.read().split("\n## ")[1:]
        stories = [[y for y in x.split("\n### Scenario:") if y != ""] for x in stories]
        return stories


def split_test_plan(test_plan):
    items = re.split(r"\d+\.", test_plan)
    # Print each item without the numbering
    return [item.strip() for item in items][1::]


def send_to_gpt(prompt: str, top_p: float = 0.5, temperature: float = 0.7, context=[]):
    client = OpenAI(api_key=OPENAI_KEY)
    response = client.chat.completions.create(
        model="gpt-4-turbo",
        top_p=top_p,
        temperature=temperature,
        messages=context + [{"role": "user", "content": prompt}],
    )
    return response.choices[0].message.content


def get_test_ideas(story: str, j: int, persona: Persona):
    print("✨ Gathering testing ideas ✨")

    @write_to_file(ideas_name(j))
    def __inner_get_test_ideas(in_j: int):
        test_ideas = send_to_gpt(
            story,
            context=test_idea_prompt(persona),
            top_p=0.3,
            temperature=0.5,
        )
        return test_ideas

    return __inner_get_test_ideas(j)


def generate_test_from(
    test_idea: str,
    story_nr: int,
    test_nr: int,
    persona=EdgeCasePersona,
    additional_prompt="",
):
    print("🤓 Generating test")

    # @write_to_file("test" + str(hash(test_idea)) + ".py")
    # Could call llm to get a decent test name i guess
    @write_to_file(test_name(story_nr, test_nr))
    def __inner_test_generation():
        res = send_to_gpt(
            test_idea + additional_prompt,
            context=python_test_prompt(persona),
            top_p=0.2,
            temperature=0.2,
        )
        if len(res) < 7:
            print("🤯 GPT-4 did not generate a valid test")
            return  # FIXME
            # raise Exception("GPT-4 did not generate a valid test")
        res = res.split("```")[1][6:]
        if res[-3:] == "```":
            res = res[:-3]
        return res

    return __inner_test_generation()


def test_name(story_nr: int, test_nr: int):
    return f"test_story_{story_nr}_test_{test_nr}.py"


def ideas_name(story_nr: int):
    # TODO could add persona name, but then would alsov have to add to test_name to make sense
    return f"test_ideas_{story_nr}.txt"


def run_test(story_nr: int, test_nr: int):
    process = subprocess.Popen(
        ["python", test_name(story_nr, test_nr)],
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
    )

    process.wait()

    exit_code = process.returncode
    output = process.stdout.read().decode("utf-8")
    error_output = process.stderr.read().decode("utf-8")

    print(f"🧪 Story {story_nr}, Test {test_nr} results:")
    # print(output)
    # print(exit_code)
    print(error_output)

    if exit_code == 0:
        print("✅ Test passed")

    if (
        "Syntax" in error_output
        or "Indentation" in error_output
        or "NameError" in error_output
    ):
        print(f"🤯 gpt made a syntax oopsie")

    if "AssertionError" in error_output:
        print("❌ Test failed")


def interactive():
    additional_prompt = ""
    story_nr = len(get_stories())

    try:
        os.remove(ideas_name(story_nr))
    except FileNotFoundError:
        pass
    while True:
        try:
            os.remove(test_name(story_nr, 0))
        except FileNotFoundError:
            break

    print("Write a user story (Ctrl-D to finish):")
    contents = []
    while True:
        try:
            line = input()
        except EOFError:
            break
        contents.append(line)

    story = "\n".join(contents)

    test_ideas = split_test_plan(get_test_ideas(story, story_nr, CyberPersona))

    for test_nr in range(len(test_ideas)):
        choice = "dummy"
        while choice.lower() != "c":
            test = generate_test_from(
                test_ideas[test_nr],
                story_nr,
                test_nr,
                additional_prompt=additional_prompt,
            )

            ## YES THIS IS FULL-BLOWN, 1:1 CODE DUPLICATION I AM SORRY
            test_syntax = Syntax(test, "python", theme="monokai", line_numbers=True)
            console = Console()
            gherkin = Markdown(story)
            idea_syn = Markdown("## Testing Idea: \n" + test_ideas[test_nr])
            console.print(Markdown(f"# Story {story_nr}, Test {test_nr}"))
            console.print(
                Columns(
                    [
                        Panel(gherkin),
                        Panel(idea_syn),
                        test_syntax,
                    ]
                )
            )

            choice = input(
                "(A)ccept [runs the test], (R)egenerate Test, (C)ontinue to next plan: "
            )
            if choice.lower() == "r":
                os.remove(test_name(story_nr, test_nr))
                additional_prompt = input(
                    "Additional prompt: "
                )  # should also contain the previous output
                if additional_prompt:
                    additional_prompt = test + additional_prompt
                continue

            if choice.lower() == "a":
                print("Running Test")
                run_test(story_nr, test_nr)
                input("Enter to continue...")
                break


def exhaustive():
    stories = ["\n".join(s) for s in get_stories()]
    for jj, story in enumerate(stories):
        test_ideas = get_test_ideas(story, jj, CyberPersona)
        for ii, idea in enumerate(split_test_plan(test_ideas)):
            generate_test_from(idea, jj, ii, CyberPersona)


def main():
    if len(sys.argv) > 1:
        if sys.argv[1][0].lower() == "e":
            exhaustive()
            return
        if sys.argv[1][0].lower() == "i":
            interactive()
            return

    # TODO expand the user studies
    stories = ["\n".join(s) for s in get_stories()]
    # TODO iterate over all test ideas
    # tests should have 2d coords (story_nr, idea_nr)

    # for story in get_stories():
    #    s = "\n".join(story)
    #    test_ideas = send_to_gpt(
    #        s, context=test_idea_prompt(), top_p=0.3, temperature=0.1
    #    )
    #    print(test_ideas)
    story_nr = 0
    test_nr = 1

    test_ideas = split_test_plan(
        get_test_ideas(stories[story_nr], story_nr, CyberPersona)
    )

    test = generate_test_from(test_ideas[test_nr], story_nr, test_nr)

    test_syntax = Syntax(test, "python", theme="monokai", line_numbers=True)
    console = Console()
    gherkin = Markdown(stories[story_nr])
    idea_syn = Markdown("## Testing Idea: \n" + test_ideas[test_nr])
    console.print(Markdown(f"# Story {story_nr}, Test {test_nr}"))
    console.print(
        Columns([Panel(gherkin), Panel("## Testing Idea: \n" + idea_syn), test_syntax])
    )

    run_test(story_nr, test_nr)

    ### USER STORY
    #   wants to generate tests for a user story on some api
    #   writes a user story
    #   gets a list of either new user stories or ideas for tests
    #   gets an overview of a pair of story and test for each idea, can accept or reject or regenerate or continue to next idea


if __name__ == "__main__":
    main()
