# %%
import mecab
print(mecab.__version__)
m = mecab.MeCab()

txts = [
    # '한편 통화정책의 완화기조 유지가 불가피한 상황에서 시중유동성이 생산적인 부문으로 유입되어 실물경제의 회복을 보다 효과적으로 뒷받침하기 위해서는 정부와 감독당국의 역할도 매우 긴요하다는 의견임.', 
    # '한편 일부 위원은 이번 회의에서 기준금리를 현 수준인 0.50%로 동결하는 것이 바람직하다는 견해를 제시하였음.',
    '신종 코로나바이러스 감염증(코로나19) 사태가 심각합니다.'
]
for t in txts:
    # print(m.parse(t))
    print(m.pos(t, join=True, flatten=False))
    print(m.pos(t, join=True, flatten=True))
    # print(m.morphs(t, flatten=False))
    # print(m.morphs(t, flatten=True))
    print(m.nouns(t, flatten=False))
    print(m.nouns(t, flatten=True))
# %%
