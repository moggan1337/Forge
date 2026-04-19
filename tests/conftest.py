"""
Test configuration and fixtures.
"""

import pytest


@pytest.fixture
def sample_typescript_code():
    """Sample TypeScript code for testing."""
    return """
interface User {
    id: number;
    name: string;
    email: string;
}

function greetUser(user: User): string {
    return `Hello, ${user.name}!`;
}

const user: User = {
    id: 1,
    name: "Alice",
    email: "alice@example.com"
};

console.log(greetUser(user));
"""


@pytest.fixture
def sample_python_code():
    """Sample Python code for testing."""
    return """
from dataclasses import dataclass
from typing import Optional

@dataclass
class User:
    id: int
    name: str
    email: str

def greet_user(user: User) -> str:
    return f"Hello, {user.name}!"

user = User(
    id=1,
    name="Alice",
    email="alice@example.com"
)

print(greet_user(user))
"""


@pytest.fixture
def sample_rust_code():
    """Sample Rust code for testing."""
    return """
#[derive(Debug)]
struct User {
    id: i32,
    name: String,
    email: String,
}

fn greet_user(user: &User) -> String {
    format!("Hello, {}!", user.name)
}

fn main() {
    let user = User {
        id: 1,
        name: String::from("Alice"),
        email: String::from("alice@example.com"),
    };

    println!("{}", greet_user(&user));
}
"""


@pytest.fixture
def sample_go_code():
    """Sample Go code for testing."""
    return """
package main

import "fmt"

type User struct {
    ID    int
    Name  string
    Email string
}

func greetUser(user User) string {
    return fmt.Sprintf("Hello, %s!", user.Name)
}

func main() {
    user := User{
        ID:    1,
        Name:  "Alice",
        Email: "alice@example.com",
    }

    fmt.Println(greetUser(user))
}
"""
