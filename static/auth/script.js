const container = document.querySelector('.container')
const registerBtn = document.querySelector('.register-btn')
const loginBtn = document.querySelector('.login-btn')


loginBtn.addEventListener('click', () =>{
    container.classList.remove('active');
})
registerBtn.addEventListener('click', () =>{
    container.classList.add('active');
})
