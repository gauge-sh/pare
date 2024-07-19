import pytest
from cli.main import setup, deploy, status, create_parser

def test_setup():
    result = setup()
    assert result == "Setup complete"

def test_deploy():
    result = deploy('test_file.txt')
    assert result == "Deploy complete with test_file.txt"

def test_status():
    result = status()
    assert result == "Status checked"

def test_parser_setup():
    parser = create_parser()
    args = parser.parse_args(['setup'])
    assert args.func(args) == "Setup complete"

def test_parser_deploy():
    parser = create_parser()
    args = parser.parse_args(['deploy', 'test_file.txt'])
    assert args.func(args) == "Deploy complete with test_file.txt"

def test_parser_status():
    parser = create_parser()
    args = parser.parse_args(['status'])
    assert args.func(args) == "Status checked"
