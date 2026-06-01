// Course interpreter utilities for completed-course recognition using deterministic aliases and fuzzy matching.
import { levenshtein, normalize } from './spellcheck.js';

const commonCourseAliases = {
  'calc 1': 'MATH 110A',
  'calculus 1': 'MATH 110A',
  'calculus one': 'MATH 110A',
  'calc 2': 'MATH 110B',
  'calculus 2': 'MATH 110B',
  'calculus two': 'MATH 110B',
  'intro micro': 'ECON 1',
  'microeconomics': 'ECON 1',
  'econ 1': 'ECON 1',
  'intro macro': 'ECON 2',
  'macroeconomics': 'ECON 2',
  'econ 2': 'ECON 2',
  'stats': 'STAT C1000',
  'statistics': 'STAT C1000',
  'intro stats': 'STAT C1000',
};

function parseCompletedCourseInputs(rawText) {
  return String(rawText || '')
    .split(/[,;\n]/)
    .map((value) => value.trim())
    .filter(Boolean);
}

function normalizeAliasKey(value) {
  return normalize(String(value || ''));
}

function addAlias(aliasMap, alias, code) {
  const key = normalizeAliasKey(alias);
  if (!key) return;
  const existing = aliasMap.get(key);
  if (existing) {
    existing.add(code);
  } else {
    aliasMap.set(key, new Set([code]));
  }
}

function buildCourseAliasMap(assistRequirements) {
  const aliasMap = new Map();

  if (assistRequirements && typeof assistRequirements === 'object') {
    for (const fromCollege of Object.keys(assistRequirements)) {
      const targets = assistRequirements[fromCollege] || {};
      for (const target of Object.keys(targets)) {
        const majors = targets[target] || {};
        for (const major of Object.keys(majors)) {
          const majorData = majors[major] || {};
          const requiredCourses = Array.isArray(majorData.requiredCourses)
            ? majorData.requiredCourses
            : [];
          for (const course of requiredCourses) {
            addAlias(aliasMap, course.code, course.code);
            addAlias(aliasMap, course.name, course.code);
            if (Array.isArray(course.aliases)) {
              for (const alias of course.aliases) {
                addAlias(aliasMap, alias, course.code);
              }
            }

            if (Array.isArray(course.satisfiedBy)) {
              for (const option of course.satisfiedBy) {
                if (Array.isArray(option)) {
                  for (const code of option) {
                    if (typeof code !== 'string') continue;
                    addAlias(aliasMap, code, code);
                    addAlias(aliasMap, code.toLowerCase(), code);
                  }
                }
              }
            }
          }
        }
      }
    }
  }

  for (const [alias, code] of Object.entries(commonCourseAliases)) {
    addAlias(aliasMap, alias, code);
  }

  return aliasMap;
}

function findExactMatch(inputKey, aliasMap) {
  return aliasMap.get(inputKey) || null;
}

function findFuzzyMatches(inputKey, aliasMap) {
  if (!inputKey) return null;
  let bestDistance = Infinity;
  const distances = new Map();

  for (const [key, codes] of aliasMap.entries()) {
    const distance = levenshtein(inputKey, key);
    if (distance > bestDistance + 2) continue;
    const existing = distances.get(distance);
    if (existing) {
      existing.push({ key, codes });
    } else {
      distances.set(distance, [{ key, codes }]);
    }
    bestDistance = Math.min(bestDistance, distance);
  }

  if (!Number.isFinite(bestDistance)) return null;

  const bestEntries = distances.get(bestDistance) || [];
  const codeSet = new Set();
  for (const entry of bestEntries) {
    for (const code of entry.codes) {
      codeSet.add(code);
    }
  }

  return {
    dist: bestDistance,
    candidates: Array.from(codeSet),
  };
}

function isFuzzyMatchAcceptable(inputKey, dist) {
  if (!inputKey) return false;
  const maxLen = Math.max(inputKey.length, 1);
  const ratio = dist / maxLen;
  if (dist === 0) return true;
  if (ratio <= 0.2) return true;
  return false;
}

function buildUncertainMatch(input, possibleMatches) {
  return {
    input,
    possibleMatches,
    message: `Which ${input} course did you complete?`,
  };
}

export function interpretCompletedCourses(rawText, assistRequirements) {
  const userInputs = parseCompletedCourseInputs(rawText);
  const aliasMap = buildCourseAliasMap(assistRequirements);
  const matchedCourses = new Set();
  const uncertainMatches = [];

  for (const originalInput of userInputs) {
    const inputKey = normalizeAliasKey(originalInput);
    if (!inputKey) continue;

    const exactCodes = findExactMatch(inputKey, aliasMap);
    if (exactCodes) {
      if (exactCodes.size === 1) {
        matchedCourses.add(Array.from(exactCodes)[0]);
        continue;
      }
      uncertainMatches.push(
        buildUncertainMatch(originalInput, Array.from(exactCodes))
      );
      continue;
    }

    const fuzzy = findFuzzyMatches(inputKey, aliasMap);
    if (fuzzy && isFuzzyMatchAcceptable(inputKey, fuzzy.dist)) {
      if (fuzzy.candidates.length === 1) {
        matchedCourses.add(fuzzy.candidates[0]);
        continue;
      }
      uncertainMatches.push(buildUncertainMatch(originalInput, fuzzy.candidates));
      continue;
    }

    if (fuzzy) {
      uncertainMatches.push(buildUncertainMatch(originalInput, fuzzy.candidates));
      continue;
    }

    uncertainMatches.push(buildUncertainMatch(originalInput, []));
  }

  return {
    matchedCourses: Array.from(matchedCourses),
    uncertainMatches,
  };
}
