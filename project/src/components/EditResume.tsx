// import React, { useState, useRef, useEffect } from 'react';
// import { useEditor, EditorContent } from '@tiptap/react';
// import Document from '@tiptap/extension-document';
// import Paragraph from '@tiptap/extension-paragraph';
// import Text from '@tiptap/extension-text';
// import Bold from '@tiptap/extension-bold';
// import Italic from '@tiptap/extension-italic';
// import Underline from '@tiptap/extension-underline';
// import Heading from '@tiptap/extension-heading';
// import * as pdfjsLib from 'pdfjs-dist';
// import { 
//   Bold as BoldIcon, 
//   Italic as ItalicIcon, 
//   Underline as UnderlineIcon,
//   Heading1,
//   Heading2,
//   Download,
//   Upload
// } from 'lucide-react';

// pdfjsLib.GlobalWorkerOptions.workerSrc = `//cdnjs.cloudflare.com/ajax/libs/pdf.js/${pdfjsLib.version}/pdf.worker.min.js`;
import React from 'react';
import { Clock, Hourglass, Loader } from 'lucide-react';

function EditResume() {
//   const [isLoading, setIsLoading] = useState(false);
//   const [error, setError] = useState<string | null>(null);
//   const fileInputRef = useRef<HTMLInputElement>(null);
//   const [, forceRender] = useState({}); // Forces component re-render

//   const editor = useEditor({
//     extensions: [
//       Document,
//       Paragraph,
//       Text,
//       Bold,
//       Italic,
//       Underline,
//       Heading.configure({
//         levels: [1, 2],
//       }),
//     ],
//     content: '',
//     editorProps: {
//       attributes: {
//         class: 'prose max-w-none focus:outline-none min-h-[500px] px-4 py-2',
//       },
//     },
//     onUpdate: () => {
//       forceRender({}); // Force re-render on editor updates
//     },
//   });

//   // Handle editor state tracking
//   useEffect(() => {
//     if (!editor) return;
  
//     const updateListener = () => {
//       forceRender({});
//     };
  
//     editor.on('transaction', updateListener);
  
//     // Cleanup function with proper void return type
//     return () => {
//       editor.off('transaction', updateListener);
//     };
//   }, [editor]); // Proper dependency array

//   const handleFileUpload = async (event: React.ChangeEvent<HTMLInputElement>) => {
//     const file = event.target.files?.[0];
//     if (!file) return;

//     try {
//       setIsLoading(true);
//       setError(null);

//       const arrayBuffer = await file.arrayBuffer();
//       const pdf = await pdfjsLib.getDocument({ data: arrayBuffer }).promise;
//       let fullText = '';

//       for (let i = 1; i <= pdf.numPages; i++) {
//         const page = await pdf.getPage(i);
//         const textContent = await page.getTextContent();
//         const pageText = textContent.items
//           .map((item: any) => item.str)
//           .join('\n'); // Preserve line breaks within paragraphs
//         fullText += pageText + '\n\n'; // Double newline between pages
//       }

//       // Convert text to structured HTML
//       const paragraphs = fullText.split(/\n\n+/g);
//       const htmlContent = paragraphs
//         .map(p => `<p>${p.replace(/\n/g, ' ').trim()}</p>`)
//         .join('');
      
//       editor?.commands.setContent(htmlContent);
//     } catch (err) {
//       setError('Failed to read PDF file');
//       console.error(err);
//     } finally {
//       setIsLoading(false);
//     }
//   };

//   const generatePDF = async () => {
//     if (!editor?.getText().trim()) {
//       setError('Please enter some content before generating PDF');
//       return;
//     }

//     try {
//       setIsLoading(true);
//       setError(null);

//       const response = await fetch('/api/generate-pdf', {
//         method: 'POST',
//         headers: {
//           'Content-Type': 'application/json',
//         },
//         body: JSON.stringify({ content: editor.getHTML() }),
//       });

//       if (!response.ok) throw new Error('Failed to generate PDF');
      
//       const blob = await response.blob();
//       const url = window.URL.createObjectURL(blob);
//       const a = document.createElement('a');
//       a.href = url;
//       a.download = 'resume.pdf';
//       document.body.appendChild(a);
//       a.click();
//       window.URL.revokeObjectURL(url);
//       document.body.removeChild(a);
//     } catch (err) {
//       setError(err instanceof Error ? err.message : 'An error occurred');
//     } finally {
//       setIsLoading(false);
//     }
//   };

//   const MenuButton = ({ 
//     onClick, 
//     isActive = false,
//     children 
//   }: { 
//     onClick: () => void;
//     isActive?: boolean;
//     children: React.ReactNode;
//   }) => (
//     <button
//       onClick={onClick}
//       className={`p-2 rounded hover:bg-gray-100 ${
//         isActive ? 'bg-gray-100 text-blue-600' : 'text-gray-700'
//       }`}
//       type="button"
//     >
//       {children}
//     </button>
//   );

//   return (
//     <div className="min-h-screen bg-gray-50 py-8 px-4">
//       <div className="max-w-5xl mx-auto">
//         <div className="bg-white rounded-lg shadow-md">
//           <div className="border-b border-gray-200 p-4">
//             <div className="flex items-center justify-between mb-4">
//               <h1 className="text-2xl font-bold text-gray-900">Resume Editor</h1>
//               <div className="flex gap-2">
//                 <button
//                   onClick={() => fileInputRef.current?.click()}
//                   disabled={isLoading}
//                   className="flex items-center px-4 py-2 rounded-md text-white bg-blue-600 hover:bg-blue-700 disabled:bg-gray-400"
//                   type="button"
//                 >
//                   <Upload className="w-4 h-4 mr-2" />
//                   Upload PDF
//                 </button>
//                 <button
//                   onClick={generatePDF}
//                   disabled={isLoading || !editor?.getText().trim()}
//                   className="flex items-center px-4 py-2 rounded-md text-white bg-green-600 hover:bg-green-700 disabled:bg-gray-400"
//                   type="button"
//                 >
//                   <Download className="w-4 h-4 mr-2" />
//                   {isLoading ? 'Processing...' : 'Download PDF'}
//                 </button>
//               </div>
//             </div>

//             <input
//               type="file"
//               ref={fileInputRef}
//               onChange={handleFileUpload}
//               accept=".pdf"
//               className="hidden"
//             />

//             <div className="flex items-center gap-1 border-t pt-4">
//               <MenuButton
//                 onClick={() => editor?.chain().focus().toggleBold().run()}
//                 isActive={editor?.isActive('bold')}
//               >
//                 <BoldIcon className="w-5 h-5" />
//               </MenuButton>
//               <MenuButton
//                 onClick={() => editor?.chain().focus().toggleItalic().run()}
//                 isActive={editor?.isActive('italic')}
//               >
//                 <ItalicIcon className="w-5 h-5" />
//               </MenuButton>
//               <MenuButton
//                 onClick={() => editor?.chain().focus().toggleUnderline().run()}
//                 isActive={editor?.isActive('underline')}
//               >
//                 <UnderlineIcon className="w-5 h-5" />
//               </MenuButton>
//               <div className="w-px h-6 bg-gray-200 mx-2" />
//               <MenuButton
//                 onClick={() => editor?.chain().focus().toggleHeading({ level: 1 }).run()}
//                 isActive={editor?.isActive('heading', { level: 1 })}
//               >
//                 <Heading1 className="w-5 h-5" />
//               </MenuButton>
//               <MenuButton
//                 onClick={() => editor?.chain().focus().toggleHeading({ level: 2 }).run()}
//                 isActive={editor?.isActive('heading', { level: 2 })}
//               >
//                 <Heading2 className="w-5 h-5" />
//               </MenuButton>
//             </div>
//           </div>

//           {error && (
//             <div className="bg-red-50 border-l-4 border-red-400 p-4">
//               <div className="flex">
//                 <div className="ml-3">
//                   <p className="text-sm text-red-700">{error}</p>
//                 </div>
//               </div>
//             </div>
//           )}

//           <div className="p-4">
//             <EditorContent editor={editor} />
//           </div>
//         </div>
//       </div>
//     </div>
//   );
return (
    <div className="min-h-screen flex items-center justify-center bg-gray-50 py-8 px-4">
      <div className="max-w-md text-center bg-white p-6 rounded-lg shadow-md">
        <h1 className="text-2xl font-bold text-gray-900 mt-4">Coming Soon</h1>
        <p className="text-gray-600 mt-2">We're working on something amazing. Stay tuned!</p>
        <div className="flex justify-center gap-4 mt-4 text-gray-500">
          <Clock className="w-6 h-6" />
          <Hourglass className="w-6 h-6" />
        </div>
      </div>
    </div>
  );
}

export default EditResume;