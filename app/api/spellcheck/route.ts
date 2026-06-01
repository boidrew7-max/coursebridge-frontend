import { NextResponse } from 'next/server';
import fs from 'fs';
import path from 'path';

function normalize(value: string) {
  return value
    .toLowerCase()
    .replace(/[^a-z0-9]/g, '')
    .trim();
}

function levenshtein(a: string, b: string) {
  if (!a.length) return b.length;
  if (!b.length) return a.length;
  const matrix: number[][] = [];
  for (let i = 0; i <= b.length; i++) {
    matrix[i] = [i];
  }
  for (let j = 0; j <= a.length; j++) {
    matrix[0][j] = j;
  }
  for (let i = 1; i <= b.length; i++) {
    for (let j = 1; j <= a.length; j++) {
      if (b.charAt(i - 1) === a.charAt(j - 1)) {
        matrix[i][j] = matrix[i - 1][j - 1];
      } else {
        matrix[i][j] = Math.min(
          matrix[i - 1][j] + 1,
          matrix[i][j - 1] + 1,
          matrix[i - 1][j - 1] + 1
        );
      }
    }
  }
  return matrix[b.length][a.length];
}

function bestMatch(input: string, candidates: string[]) {
  const nInput = normalize(input);
  let best = null as null | { candidate: string; dist: number };
  for (const c of candidates) {
    const nC = normalize(c);
    const d = levenshtein(nInput, nC);
    if (best === null || d < best.dist) best = { candidate: c, dist: d };
  }
  return best;
}

export async function POST(req: Request) {
  try {
    const body = await req.json();
    const inputs: string[] = Array.isArray(body.courses) ? body.courses : [];

    // Load articulation JSON (browser-safe) as source of known course names
    const jsonPath = path.join(process.cwd(), 'public', 'data', 'assist_articulations.json');
    const raw = fs.readFileSync(jsonPath, 'utf8');
    const data = JSON.parse(raw);

    // Build candidate set from assist data: include community college course names and target requirement codes
    const candidates = new Set<string>();
    if (data.assistRequirements) {
      for (const fromCollege of Object.keys(data.assistRequirements)) {
        const targets = data.assistRequirements[fromCollege];
        for (const targetUniv of Object.keys(targets)) {
          const majors = targets[targetUniv];
          for (const major of Object.keys(majors)) {
            const majorData = majors[major];
            if (!majorData) continue;
            const reqs = majorData.requiredCourses || [];
            for (const r of reqs) {
              if (r.code) candidates.add(r.code);
              if (Array.isArray(r.satisfiedBy)) {
                r.satisfiedBy.forEach((s: string) => { if (s) candidates.add(s); });
              }
            }
          }
        }
      }
    }

    const candidateList = Array.from(candidates);

    const results = inputs.map((input) => {
      const match = bestMatch(input, candidateList);
      if (!match) return { input, suggestion: null, confidence: 'none' };

      // Decide confidence by normalized distance ratio
      const nInput = normalize(input);
      const nBest = normalize(match.candidate);
      const maxLen = Math.max(nInput.length, nBest.length) || 1;
      const ratio = match.dist / maxLen;
      let confidence: 'high' | 'medium' | 'low' = 'low';
      if (ratio === 0) confidence = 'high';
      else if (ratio <= 0.25) confidence = 'medium';
      else confidence = 'low';

      return {
        input,
        suggestion: match.candidate,
        distance: match.dist,
        ratio,
        confidence,
      };
    });

    return NextResponse.json({ results });
  } catch (err: any) {
    return NextResponse.json({ error: String(err) }, { status: 500 });
  }
}
