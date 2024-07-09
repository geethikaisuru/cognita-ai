import { NextResponse } from 'next/server';
import { exec } from 'child_process';
import fs from 'fs';
import path from 'path';
import { promisify } from 'util';

const writeFileAsync = promisify(fs.writeFile);
const execAsync = promisify(exec);

export async function POST(request: Request) {
  try {
    const { files } = await request.json();
    const uploadDir = path.join(process.cwd(), 'uploads');

    if (!fs.existsSync(uploadDir)) {
      fs.mkdirSync(uploadDir, { recursive: true });
    }

    const filePaths = [];

    for (let i = 0; i < files.length; i++) {
      const fileName = `input${i}.pdf`;
      const filePath = path.join(uploadDir, fileName);
      await writeFileAsync(filePath, Buffer.from(files[i], 'base64'));
      filePaths.push(filePath);
    }

    const pythonScript = path.join(process.cwd(), 'PGen2.py');
    const command = `python "${pythonScript}" ${filePaths.map(f => `"${f}"`).join(' ')}`;

    const { stdout, stderr } = await execAsync(command);

    if (stderr) {
      console.error(`stderr: ${stderr}`);
    }
    console.log(`stdout: ${stdout}`);

    const outputPath = path.join(process.cwd(), 'localmodelpaperStyledPhi3.pdf');
    const pdfContent = await fs.promises.readFile(outputPath);
    const base64Pdf = pdfContent.toString('base64');

    return NextResponse.json({ pdf: base64Pdf }, { status: 200 });

  } catch (error) {
    console.error('Error:', error);
    return NextResponse.json({ error: 'Failed to generate paper' }, { status: 500 });
  }
}

export const config = {
  api: {
    bodyParser: {
      sizeLimit: '10mb',
    },
  },
};