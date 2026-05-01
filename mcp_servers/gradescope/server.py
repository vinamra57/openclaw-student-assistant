"""
Gradescope MCP server (best-effort).

Gradescope has no public API. This server wraps the gradescopeapi library
which uses web scraping. It is inherently fragile and may break at any time.

The preferred approach is to get Gradescope grades through Canvas LTI sync.
This server is a fallback for courses that don't have LTI configured.

Usage:
    GRADESCOPE_EMAIL=<email> GRADESCOPE_PASSWORD=<password> \
        python -m mcp_servers.gradescope.server
"""

import logging
import os

from mcp.server.fastmcp import FastMCP

logger = logging.getLogger(__name__)

mcp = FastMCP("Gradescope")


def _get_credentials() -> tuple[str, str]:
    email = os.environ.get("GRADESCOPE_EMAIL", "")
    password = os.environ.get("GRADESCOPE_PASSWORD", "")
    return email, password


@mcp.tool()
def get_gradescope_courses() -> str:
    """List courses the student is enrolled in on Gradescope.

    Returns course names and IDs.
    """
    email, password = _get_credentials()
    if not email or not password:
        return "Gradescope is not configured. Set GRADESCOPE_EMAIL and GRADESCOPE_PASSWORD."

    try:
        from gradescopeapi.classes.connection import GSConnection

        conn = GSConnection()
        conn.login(email, password)
        courses = conn.get_courses()
        if not courses:
            return "No courses found on Gradescope."

        lines = [f"Found {len(courses)} course(s):\n"]
        for course in courses:
            lines.append(
                f"- {course.get('name', 'Unknown')} (ID: {course.get('id', '?')})"
            )
        return "\n".join(lines)

    except ImportError:
        return "gradescopeapi is not installed. Install with: pip install gradescopeapi"
    except Exception as e:
        logger.error(f"Gradescope error: {e}")
        return f"Failed to fetch Gradescope courses: {e}"


@mcp.tool()
def get_gradescope_assignments(course_id: str) -> str:
    """List assignments and grades for a Gradescope course.

    Args:
        course_id: The Gradescope course ID
    """
    email, password = _get_credentials()
    if not email or not password:
        return "Gradescope is not configured. Set GRADESCOPE_EMAIL and GRADESCOPE_PASSWORD."

    try:
        from gradescopeapi.classes.connection import GSConnection

        conn = GSConnection()
        conn.login(email, password)
        assignments = conn.get_assignments(course_id)
        if not assignments:
            return f"No assignments found for course {course_id}."

        lines = [f"Assignments for course {course_id}:\n"]
        for a in assignments:
            name = a.get("name", "Unknown")
            score = a.get("score", "—")
            max_score = a.get("max_score", "—")
            status = a.get("status", "")
            lines.append(f"- {name}: {score}/{max_score} ({status})")
        return "\n".join(lines)

    except ImportError:
        return "gradescopeapi is not installed. Install with: pip install gradescopeapi"
    except Exception as e:
        logger.error(f"Gradescope error: {e}")
        return f"Failed to fetch assignments: {e}"


if __name__ == "__main__":
    mcp.run()
