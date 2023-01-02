from flask import Flask, render_template

def get_error(id):
    return render_template('error.html')
    
