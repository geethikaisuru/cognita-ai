import React, { useState } from 'react';

   const PdfGenerator: React.FC = () => {
     const [files, setFiles] = useState<File[]>([]);
     const [pdfUrl, setPdfUrl] = useState<string | null>(null);

     const handleFileChange = (event: React.ChangeEvent<HTMLInputElement>) => {
       if (event.target.files) {
         setFiles(Array.from(event.target.files));
       }
     };

     const handleSubmit = async (event: React.FormEvent<HTMLFormElement>) => {
       event.preventDefault();
       
       const formData = new FormData();
       files.forEach((file, index) => {
         formData.append(`file${index}`, file);
       });

       try {
         const response = await fetch('/api/generate', {
           method: 'POST',
           body: formData,
         });

         if (!response.ok) {
           throw new Error('Failed to generate PDF');
         }

         const data = await response.json();
         const base64Pdf = data.pdf;

         const blob = new Blob([Buffer.from(base64Pdf, 'base64')], { type: 'application/pdf' });
         const url = URL.createObjectURL(blob);

         setPdfUrl(url);
       } catch (error) {
         console.error('Error generating PDF:', error);
       }
     };

     return (
       <div>
         <form onSubmit={handleSubmit}>
           <input type="file" multiple onChange={handleFileChange} accept=".pdf" />
           <button type="submit" disabled={files.length === 0}>Generate PDF</button>
         </form>

         {pdfUrl && (
           <a href={pdfUrl} download="generated_paper.pdf">
             <button>Download Generated PDF</button>
           </a>
         )}
       </div>
     );
   };

   export default PdfGenerator;