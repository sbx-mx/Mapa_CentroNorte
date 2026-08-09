(() => {
  const form=document.getElementById('uploadForm'); const result=document.getElementById('uploadResult');
  if(!form) return;
  form.addEventListener('submit',async event=>{
    event.preventDefault(); result.className='status'; result.textContent='Validando archivo…';
    try{ const response=await fetch('/administrar/importar',{method:'POST',body:new FormData(form)}); const payload=await response.json(); if(!response.ok) throw new Error((payload.errors||['Error de actualización']).join(' · ')); result.classList.add('success'); result.textContent=payload.message; }
    catch(error){ result.classList.add('error'); result.textContent=error.message; }
  });
})();

