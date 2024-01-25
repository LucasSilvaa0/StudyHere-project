from django.shortcuts import render, redirect
from django.http import HttpResponse, Http404
from .models import Categoria, Flashcard, Desafio, FlashcardDesafio
from django.contrib.messages import constants
from django.contrib import messages

def novo_flashcard(request):
    if not request.user.is_authenticated:
        return redirect('/usuarios/logar')
    
    if request.method == 'GET':
        categorias = Categoria.objects.all()
        dificuldades = Flashcard.DIFICULDADE_CHOICES
        flashcards = Flashcard.objects.filter(user=request.user)
        
        categoria_filtrar = request.GET.get('categoria')
        dificuldade_filtrar = request.GET.get('dificuldade')
        
        if categoria_filtrar:
            flashcards = flashcards.filter(categoria__id=categoria_filtrar)
        if dificuldade_filtrar:
            flashcards = flashcards.filter(dificuldade=dificuldade_filtrar)
        
        return render(request, 'novo_flashcard.html', {'categorias': categorias, 'dificuldades': dificuldades, 'flashcards':flashcards})
    elif request.method == 'POST':
        pergunta = request.POST.get('pergunta')
        resposta = request.POST.get('resposta')
        categoria = request.POST.get('categoria')
        dificuldade = request.POST.get('dificuldade')
        
        if len(pergunta.strip()) == 0 or len(resposta.strip()) == 0:
            messages.add_message(request, constants.ERROR, 'Preencha os campos de pergunta e resposta')
            return redirect('/flashcard/novo_flashcard')
        
        flashcard = Flashcard(
            user=request.user,
            pergunta = pergunta,
            resposta = resposta,
            categoria_id = categoria,
            dificuldade = dificuldade
        )
        
        flashcard.save()
        
        flashcards = Flashcard.objects.filter(user=request.user)
        
        messages.add_message(request, constants.SUCCESS, 'Flashcard cadastrado com sucesso')
        
        return redirect('/flashcard/novo_flashcard', {'flashcards':flashcards})

def deletar_flashcard(request, id):
    flashcard = Flashcard.objects.get(id=id)
    
    if flashcard.user_id == request.user.id:
        flashcard_desafio = FlashcardDesafio.objects.filter(flashcard__id=id)
        for f in flashcard_desafio:
            f.delete()
            
        flashcard.delete()
        
        messages.add_message(request, constants.SUCCESS, "Flahscard deletado com sucesso!")

    return redirect('/flashcard/novo_flashcard')

def iniciar_desafio(request):
    if request.method == 'GET':
        categorias = Categoria.objects.all()
        dificuldades = Flashcard.DIFICULDADE_CHOICES
        return render(request, 'iniciar_desafio.html', {'categorias': categorias, 'dificuldades': dificuldades})
    elif request.method == 'POST':
        titulo = request.POST.get('titulo')
        categorias = request.POST.getlist('categoria')
        dificuldade = request.POST.get('dificuldade')
        qtd_perguntas = request.POST.get('qtd_perguntas')
        
        flashcards = (
            Flashcard.objects.filter(user=request.user)
            .filter(dificuldade=dificuldade)
            .filter(categoria_id__in=categorias)
            .order_by('?')
        )
        
        if flashcards.count() < int(qtd_perguntas):
            return redirect('/flashcard/iniciar_desafio')
        
        desafio = Desafio(
            user = request.user,
            titulo = titulo,
            quantidade_perguntas = qtd_perguntas,
            dificuldade = dificuldade,
            status = 'P'
        )
        
        desafio.save()
        
        for categoria in categorias:
            desafio.categoria.add(categoria)
        
        flashcards = flashcards[:int(qtd_perguntas)]
        
        for f in flashcards:
            flashcard_desafio = FlashcardDesafio(
                flashcard = f
            )
            flashcard_desafio.save()
            desafio.flashcards.add(flashcard_desafio)
        
        desafio.save()
        
        return redirect('/flashcard/listar_desafio')

def listar_desafio(request):
    desafios = Desafio.objects.filter(user=request.user)
    
    categorias = Categoria.objects.all()
    dificuldades = Flashcard.DIFICULDADE_CHOICES
    
    categoria_filtrar = request.GET.get('categoria')
    dificuldade_filtrar = request.GET.get('dificuldade')
    
    if categoria_filtrar:
        categoria_filtrar = Categoria.objects.get(id=categoria_filtrar)
        for d in desafios.all():
            if categoria_filtrar not in list(d.categoria.all()):
                desafios = desafios.exclude(id=d.id)

    if dificuldade_filtrar:
        desafios = desafios.filter(dificuldade=dificuldade_filtrar)
    
    return render(request, 'listar_desafio.html', {'desafios': desafios, 'categorias':categorias, 'dificuldades':dificuldades})

def desafio(request, id):
    desafio = Desafio.objects.get(id=id)
    
    if not desafio.user == request.user:
        raise Http404()
        
    if request.method == "GET":
        categorias = desafio.categoria.all()
        faltantes = desafio.flashcards.filter(respondido=0).count()
        erros = desafio.flashcards.filter(acertou=0).count() - faltantes
        acertos = desafio.flashcards.filter(acertou=1).count()
        
        if faltantes == 0:
            desafio.status = 'R'
            desafio.save()
            
        return render(request, "desafio.html", {"desafio":desafio, "acertos":acertos, "erros":erros, "faltantes":faltantes, "categorias": categorias})
    return HttpResponse(id)

def responder_flashcard(request, id):
    flashcard_desafio = FlashcardDesafio.objects.get(id=id)
    acertou = request.GET.get('acertou')
    desafio_id = request.GET.get('desafio_id')
    
    if not flashcard_desafio.flashcard.user == request.user:
        raise Http404()
        
    flashcard_desafio.respondido = True
    flashcard_desafio.acertou = True if acertou == "1" else False
    
    flashcard_desafio.save()
    
    
    return redirect(f'/flashcard/desafio/{desafio_id}')

def relatorio(request, id):
    desafio = Desafio.objects.get(id=id)
    
    acertos = desafio.flashcards.filter(acertou=1).count()
    erros = desafio.flashcards.count() - acertos
    dados = [acertos, erros]
    
    categorias = desafio.categoria.all()
    lista_categorias = []
    lista_acertos = []
    for c in categorias:
        lista_categorias.append(c.nome)
        lista_acertos.append(desafio.flashcards.filter(flashcard__categoria=c).filter(acertou=1).count())
        
        
    lista_acertos_ordenada = sorted(lista_acertos, reverse=True)
    cont = 0
    tamanho = len(lista_acertos_ordenada)
    lista_tuplas_ordenada = []
    print(lista_acertos_ordenada)
    while cont < tamanho:
        for c in categorias:
            if cont == tamanho:
                break
            
            i = desafio.flashcards.filter(flashcard__categoria=c).filter(acertou=1).count()
            if i == lista_acertos_ordenada[cont]:
                lista_tuplas_ordenada.append((c.nome, i, desafio.flashcards.filter(flashcard__categoria=c).count() - i))
                cont += 1
    
    return render(request, 'relatorio.html', {'desafio': desafio, 'dados': dados, 'lista_categorias': lista_categorias, 'lista_acertos': lista_acertos, 'lista_tuplas_ordenada': lista_tuplas_ordenada})