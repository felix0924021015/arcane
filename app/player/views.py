from app.models import Card, History, is_player
from app.player.forms import FeedForm
from django.contrib.auth.decorators import login_required
from django.contrib.auth.models import User
from django.core.exceptions import ObjectDoesNotExist, PermissionDenied
from django.shortcuts import redirect, render
from django.db import transaction


def player(request, id=None):
    if not request.user.is_authenticated():
        return redirect("login", id)
    else:
        if not id == request.user.username:
            # rediect logged-in user to /player/<username>
            return redirect('player data', request.user.username)
        if not is_player(request.user):
            # ban non player
            raise PermissionDenied
        else:
            user = request.user
            records = History.objects.filter(user=user)
            return render(request, 'player/player.html',
                          {"user": user, "records": records})


@login_required
def feed(request, id=None):
    if not request.user.is_staff:
        raise PermissionDenied
    else:
        try:
            user = User.objects.get(username=id)
        except ObjectDoesNotExist:
            return render(
                request, "submit.html", {
                    "content": "你是誰？",
                    "title": "錯誤！"}, status=404)

        if not is_player(user):
            return render(
                request, "submit.html", {
                    "content": "工作人員的世界你是看不到的!",
                    "title": "錯誤！"}, status=404)
        else:
            if not request.POST:
                form = FeedForm()
                return render(request, "player/feed.html", locals())
            else:
                form = FeedForm(request.POST)
                if form.is_valid():
                    with transaction.atomic():
                        player = user.player
                        card = form.cleaned_data["card"]
                        card.capturer = player
                        card.retrieved = True
                        card.save()
                        record_sender = History(
                            action=0xfeed, user=request.user, card=card,
                            comment="給了 %s (%s)" % (player.user.get_full_name(), player.user.username))
                        record_sender.save()
                        record_reciever = History(
                            action=0xfeed, user=player.user, card=card,
                            comment="從 %s 收到一張卡片" % request.user.get_full_name())
                        record_reciever.save()

                    return render(
                        request, "submit.html", {
                            "title": "成功發送",
                            "content": "你送給 %s 一張卡片" % player.user.get_full_name(),
                        })
                else:
                    return render(request, "player/feed.html", locals())
