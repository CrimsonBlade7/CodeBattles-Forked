import type { ProblemCard } from '../store/gameStore'
import { loadPyodide, type PyodideInterface } from 'pyodide'

type JudgeResult = { passed: boolean; testResults: any[]; error: string | null }

let pyodidePromise: Promise<PyodideInterface> | null = null

async function getPyodide(): Promise<PyodideInterface> {
  if (!pyodidePromise) {
    const indexURL =
      import.meta.env.VITE_PYODIDE_INDEX_URL ||
      'https://cdn.jsdelivr.net/pyodide/v0.26.2/full/'
    pyodidePromise = loadPyodide({ indexURL })
  }
  return pyodidePromise
}

function extractFunctionName(functionSignature: string): string {
  const sig = functionSignature.trim()
  if (!sig.startsWith('def ')) {
    throw new Error("Invalid function signature (expected to start with 'def ')")
  }
  const head = sig.split('(')[0]
  const name = head.replace('def ', '').trim()
  if (!/^[A-Za-z_][A-Za-z0-9_]*$/.test(name)) {
    throw new Error('Invalid function name in signature')
  }
  return name
}

export async function judgePythonSubmission(args: {
  code: string
  card: ProblemCard
}): Promise<JudgeResult> {
  const { code, card } = args
  const pyodide = await getPyodide()

  const functionName = extractFunctionName(card.problem.functionSignature)
  const payload = {
    code,
    functionName,
    testCases: card.problem.testCases,
  }

  // Pass data into Python without interpolating user code into the harness string.
  pyodide.globals.set('__payload', payload)

  const harness = `
import json

payload = __payload.to_py()
code = payload["code"]
function_name = payload["functionName"]
test_cases = payload["testCases"]

test_results = []

try:
    # Execute user code in a fresh globals dict to avoid leaking our harness symbols.
    user_globals = {}
    exec(code, user_globals, user_globals)

    if function_name not in user_globals or not callable(user_globals[function_name]):
        raise Exception(f"Submitted code did not define callable '{function_name}'")

    fn = user_globals[function_name]

    for tc in test_cases:
        input_dict = tc.get("input", {})
        expected = tc.get("expectedOutput", None)
        try:
            actual = fn(**input_dict)
            passed = actual == expected
            test_results.append({
                "passed": passed,
                "input": input_dict,
                "expected": expected,
                "actual": actual,
            })
        except Exception as e:
            test_results.append({
                "passed": False,
                "input": input_dict,
                "expected": expected,
                "actual": None,
                "error": str(e),
            })

    all_passed = all(r.get("passed", False) for r in test_results) if test_results else False
    result = {"passed": all_passed, "testResults": test_results, "error": None}
except Exception as e:
    result = {"passed": False, "testResults": [], "error": str(e)}

json.dumps(result)
`

  try {
    const jsonStr = await pyodide.runPythonAsync(harness)
    const parsed = JSON.parse(String(jsonStr))
    return {
      passed: Boolean(parsed.passed),
      testResults: Array.isArray(parsed.testResults) ? parsed.testResults : [],
      error: parsed.error ?? null,
    }
  } catch (e) {
    return {
      passed: false,
      testResults: [],
      error: e instanceof Error ? e.message : String(e),
    }
  } finally {
    // Best-effort cleanup
    try {
      pyodide.globals.delete('__payload')
    } catch {
      // ignore
    }
  }
}

