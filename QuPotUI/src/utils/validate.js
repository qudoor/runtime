export function isExternal(path) {
  return /^(https?:|mailto:|tel:)/.test(path)
}


export const isHTMLString = (str) => {
  let div = document.createElement('div');
  div.innerHTML = str;
  for (let child of div.childNodes) {
    if (child.nodeType === Node.ELEMENT_NODE) {
      return true;
    }
  }
  return false;
}
