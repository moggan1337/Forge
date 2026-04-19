"""
Example usage of Forge transpiler.
"""

from forge import Transpiler, TranspilerConfig, Language


# Example 1: Basic TypeScript to Python transpilation
def example_typescript_to_python():
    """Convert TypeScript to Python."""
    config = TranspilerConfig(
        source_language=Language.TYPESCRIPT,
        target_language=Language.PYTHON,
    )
    transpiler = Transpiler(config)

    typescript_code = """
interface User {
    id: number;
    name: string;
    email: string;
}

function createUser(name: string, email: string): User {
    return {
        id: Math.random(),
        name: name,
        email: email
    };
}

const user = createUser("Alice", "alice@example.com");
console.log(user.name);
"""

    result = transpiler.transpile(typescript_code)
    print("=== TypeScript to Python ===")
    print(result.output)
    print()


# Example 2: Python to TypeScript
def example_python_to_typescript():
    """Convert Python to TypeScript."""
    config = TranspilerConfig(
        source_language=Language.PYTHON,
        target_language=Language.TYPESCRIPT,
    )
    transpiler = Transpiler(config)

    python_code = """
from dataclasses import dataclass
from typing import List, Optional

@dataclass
class User:
    name: str
    email: str
    age: Optional[int] = None

def get_user_names(users: List[User]) -> List[str]:
    return [user.name for user in users]

users = [
    User(name="Alice", email="alice@example.com", age=30),
    User(name="Bob", email="bob@example.com")
]

names = get_user_names(users)
print(names)
"""

    result = transpiler.transpile(python_code)
    print("=== Python to TypeScript ===")
    print(result.output)
    print()


# Example 3: TypeScript to Rust
def example_typescript_to_rust():
    """Convert TypeScript to Rust."""
    config = TranspilerConfig(
        source_language=Language.TYPESCRIPT,
        target_language=Language.RUST,
    )
    transpiler = Transpiler(config)

    typescript_code = """
interface Point {
    x: number;
    y: number;
}

function distance(p1: Point, p2: Point): number {
    const dx = p2.x - p1.x;
    const dy = p2.y - p1.y;
    return Math.sqrt(dx * dx + dy * dy);
}

const origin: Point = { x: 0, y: 0 };
const point: Point = { x: 3, y: 4 };
console.log(distance(origin, point));
"""

    result = transpiler.transpile(typescript_code)
    print("=== TypeScript to Rust ===")
    print(result.output)
    print()


# Example 4: Batch transpilation
def example_batch_transpilation():
    """Transpile multiple files."""
    config = TranspilerConfig(
        source_language=Language.TYPESCRIPT,
        target_language=Language.PYTHON,
    )
    transpiler = Transpiler(config)

    files = [
        ("types.ts", """
export interface User {
    id: number;
    name: string;
}
"""),
        ("utils.ts", """
export function greet(name: string): string {
    return `Hello, ${name}!`;
}
"""),
    ]

    print("=== Batch Transpilation ===")
    for filename, content in files:
        result = transpiler.transpile(content)
        print(f"--- {filename} -> {filename.replace('.ts', '.py')} ---")
        print(result.output)
        print()


if __name__ == "__main__":
    example_typescript_to_python()
    example_python_to_typescript()
    example_typescript_to_rust()
    example_batch_transpilation()
