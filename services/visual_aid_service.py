import re
import urllib.parse

DIAGRAM_INSTRUCTION = """

Also include a Mermaid.js diagram summarizing the structure/process here.
Wrap ONLY the diagram code in a fenced block starting with ```mermaid and
ending with ```. Follow these rules exactly, or the diagram will fail to
render:
- Start with exactly: flowchart TD
- Each line after that must be exactly: NodeID[Label] --> NodeID2[Label2]
- NodeID must be a short single word with no spaces (e.g. A, B, Step1).
- Label text must NOT contain any of these characters: ( ) " ' : ; { } [ ] |
- Use plain words and numbers only in labels, 2-5 words each.
- No subgraphs, no styling, no comments, no blank lines, no markdown.
- 4 to 8 nodes total.
Put nothing else inside that code block.
"""


def with_diagram_request(prompt):
    """Appends a standard instruction asking the AI to include a Mermaid diagram."""
    return prompt + DIAGRAM_INSTRUCTION


def sanitize_mermaid(code):
    """
    Best-effort cleanup of common LLM mistakes in generated Mermaid code,
    and a final validity check. Returns "" if the result still looks too
    broken to safely render (better to show nothing than a visible error).
    """
    if not code:
        return ""

    lines = [line.strip() for line in code.splitlines() if line.strip()]
    lines = [line for line in lines if not line.startswith("%%")]  # strip comments

    if not lines:
        return ""

    # Make sure it actually starts with a supported diagram type.
    first = lines[0].lower()
    if not (first.startswith("flowchart") or first.startswith("graph")):
        lines.insert(0, "flowchart TD")

    # Strip characters known to break Mermaid's parser when the LLM ignores
    # the "no special characters" instruction — but NOT < or >, since
    # those are part of the arrow syntax itself (-->, <--).
    cleaned = []
    for line in lines:
        line = re.sub(r'["\'(){}|]', "", line)
        cleaned.append(line)

    result = "\n".join(cleaned)

    # A diagram needs at least one real connection to be worth rendering.
    if "-->" not in result:
        return ""

    return result


def extract_diagram(raw_text):
    """
    Pulls a fenced ```mermaid ... ``` block out of an AI response, cleans
    it up, and returns (remaining_text, mermaid_code). mermaid_code is ""
    if none was found or it couldn't be salvaged into something renderable.
    """
    match = re.search(r"```mermaid\s*(.*?)```", raw_text, re.DOTALL)

    if not match:
        return raw_text, ""

    mermaid_code = sanitize_mermaid(match.group(1).strip())
    remaining_text = (raw_text[:match.start()] + raw_text[match.end():]).strip()

    return remaining_text, mermaid_code


def build_illustration_url(concept):
    """
    Builds a Pollinations.ai image URL for a concept — free, no API key,
    loaded directly by the browser so it doesn't need server-side network
    access. See https://pollinations.ai
    """
    image_prompt = f"educational illustration of {concept}, colorful, clear, digital art, for students"
    return "https://image.pollinations.ai/prompt/" + urllib.parse.quote(image_prompt)


def add_visuals(prompt, concept, want_visuals):
    """
    Convenience wrapper for route handlers: if want_visuals is truthy,
    appends the diagram instruction to the prompt and returns an
    illustration URL; otherwise returns the prompt unchanged and no image.
    Call extract_diagram() on the AI's response afterward either way.
    """
    if not want_visuals:
        return prompt, ""

    return with_diagram_request(prompt), build_illustration_url(concept)
